import csv
import os
import ntpath
import pandas as pd
import numpy as np
from ntpath import basename
from xmlutils.xmltable2csv import xmltable2csv


class XmlConverter:

    TABLE_NAMES = ('General', 'Segments',
                   'Strain Traces 2CH', 'Strain Traces 4CH', 'Strain Traces APLAX',
                   'Work Traces 2CH', 'Work Traces 4CH', 'Work Traces APLAX',
                   'Fibre Stress Traces 2CH', 'Fibre Stress Traces 4CH', 'Fibre Stress Traces APLAX',
                   'Pressure Trace', 'Global Traces')
    STRAIN_TABLES = ('Strain Traces 2CH', 'Strain Traces 4CH','Strain Traces APLAX',)

    def __init__(self, xml_file, csv_file):
        self.xml_file = xml_file
        self.csv_file = csv_file
        self.tables = {}
        self.dataframes = {}
        self.index = None

    def xml2rawcsv(self):
        """
        Convert the xml into a raw csv file.
        """
        converter = xmltable2csv(input_file=self.xml_file, output_file=self.csv_file)
        converter.convert(tag='Data')

    def build_separate_tables(self):
        """
        Transform raw csv into a dictionary with lists of lists containing the data.
        """
        _table_number = 0
        _current_table = []

        with open(self.csv_file, newline='') as csvfile:
            data_table = csv.reader(csvfile, delimiter=',', quotechar='\'')
            for row in list(data_table):
                if row[0] == 'Time' or row[0] == '' and row[1 != '']:
                    self.tables[self.TABLE_NAMES[_table_number]] = _current_table
                    _table_number += 1
                    _current_table = row
                else:
                    _current_table.append(row)
        self.tables[self.TABLE_NAMES[_table_number]] = _current_table  # last table
        os.remove(self.csv_file)  # Since the kernel function writes the csv be default, it has to be removed

    # -----ParseListToDataFrames----------------------------------------------------------------------------------------

    @staticmethod
    def _assemble_separate_strings(table):
        """
        Sometimes XML converter leaves separate strings, i.e. column names, which cannot be transformed directly into
        a dataframe. The funcion appends them in a list.
        :param table: List of lists and strings, returned by the xml2csv converter.
        :return: A list of lists with structure enabling the data frame transformation.
        """
        _appended_values = [string for string in table if isinstance(string, str)]  # append strings into list
        table = [_list for _list in table if isinstance(_list, list)]  # remove single strings
        table.insert(0, _appended_values)

        return table

    def _parse_general(self):
        """
        Parse the General table. Contains basic data: id, blood pressure, valve opening times in milliseconds,
        ejection fraction and mean work measurements.
        """
        df_general = pd.DataFrame(self.tables['General'])
        df_general = df_general.T
        df_general.columns = df_general.iloc[0]
        df_general = df_general.reindex(df_general.index.drop(0))
        df_general['SBP'] = df_general['BP'][1]
        df_general['DBP'] = df_general['BP'][2]
        df_general = df_general.dropna(axis='index')
        df_general = df_general.drop(columns=['Name', 'BP'])
        df_general = df_general.set_index('ID')
        df_general = df_general.astype(float)

        self.index = df_general.index.values
        self.dataframes['General'] = df_general

    def _parse_segments(self):
        """
        Parse the Segments table. The data is flattened so that each value is in a seperate column.
        """
        _table = self.tables['Segments']
        _table = self._assemble_separate_strings(_table)

        df_segments = pd.DataFrame(_table[1:], columns=_table[0])
        df_segments = df_segments.set_index('')
        if 'Status' in df_segments.index:
            df_segments = df_segments.drop(index='Status')
        df_segments = df_segments.astype(float)
        df_segments = self._flatten_df(df_segments)

        self.dataframes['Segments'] = df_segments

    def _parse_trace_table(self, table_name):
        """
        Parse a trace table. Strain, work and fibre stress tables have the same structures.
        :param table_name: String, one of the elements of TABLE_NAMES
        """
        _table = self.tables[table_name]
        _table = self._assemble_separate_strings(_table)

        df_trace = pd.DataFrame(_table[1:], columns=_table[0]).astype(float)
        df_trace = df_trace.set_index('Time')

        self.dataframes[table_name] = df_trace

    def _parse_all_trace_tables(self):
        """
        Parse all traces with common structure with Time as index.
        """
        for table_name in self.TABLE_NAMES[2:-1]:
            self._parse_trace_table(table_name)

    def _parse_global_table(self):
        """
        Parse the global traces table. Builds a list of strain, work, and fibre stress data frames, indexed by Time.
        """
        _table = self.tables['Global Traces']
        _table = self._assemble_separate_strings(_table)

        df_global = pd.DataFrame(_table[1:], columns=_table[0])

        df_global_strain = df_global.iloc[:, 0:2]
        df_global_strain = df_global_strain[df_global_strain.Time != ''].astype(float)  # drop empty rows
        df_global_strain = df_global_strain.set_index('Time')
        df_global_work = df_global.iloc[:, 3:5].astype(float)
        df_global_work = df_global_work.set_index('Time')
        df_global_fibre_stress = df_global.iloc[:, 6:8].astype(float)
        df_global_fibre_stress = df_global_fibre_stress.set_index('Time')

        self.dataframes['Global Traces'] = [df_global_strain, df_global_work, df_global_fibre_stress]

    def _parse_all_tables(self):
        """
        Get all tables into a single pandas data frame. The result is kept in the self.dataframes structure.
        """
        self._parse_general()
        self._parse_segments()
        self._parse_all_trace_tables()
        self._parse_global_table()

    # -----END-ParseListToDataFrames------------------------------------------------------------------------------------

    # -----GlobalStrains------------------------------------------------------------------------------------------------

    def _calculate_global_longitudinal_strains(self):

        df_globals = pd.DataFrame()

        for i, trace in enumerate(self.STRAIN_TABLES):
            df = self.dataframes[trace]
            global_strain = df.mean(axis=1)
            global_strain = global_strain.reset_index(level=0)
            df_globals['Time_' + trace[14:]] = global_strain.iloc[:, 0]
            df_globals['global_strain_' + trace[14:]] = global_strain.iloc[:, 1]

        return df_globals

    def save_global_longitudinal_strains(self, gls_path=''):

        gls = self._calculate_global_longitudinal_strains()
        gls_output_file = ntpath.basename(self.csv_file).split('.')[0]
        gls_file_path = os.path.join(gls_path, gls_output_file + '_mean_global_traces.csv')
        gls.to_csv(gls_file_path)

    def _get_gls_ge(self):

        avc_time = 0.001 * self.dataframes['General'].loc[self.index, 'AVC'].values[0]
        avc_view = self.dataframes['Global Traces'][0].index[np.argmin(np.abs(
            self.dataframes['Global Traces'][0].index.values - avc_time))]

        df = self.dataframes['Global Traces'][0]
        df_before_avc = df.loc[:avc_view]
        df_before_avc.append(df.loc[[avc_view]])
        max_global_strain_before_avc = df_before_avc.min(axis='rows')
        max_global_strain = df.min(axis='rows')

        dict_gls = {'max_gls_before_avc': max_global_strain_before_avc, 'max_gls': max_global_strain,
                    'max_gls_time': df.index[df['Global strain'].values == max_global_strain.values][0]}

        df_gls = pd.DataFrame(dict_gls)
        df_gls.set_index(self.dataframes['General'].index, inplace=True)

        self.dataframes['Global Descriptors'] = df_gls

    # -----END-GlobalStrains--------------------------------------------------------------------------------------------

    # -----StrainDescriptors--------------------------------------------------------------------------------------------

    def _find_strain_descriptors(self):

        # TODO: in trace tables, the time is kept in seconds, yet in the general table, valve actions are given in
        # TODO milliseconds. It makes sense to bring them to the same unit
        # TODO IMPORTANT!!! keep the frame rate in mind.

        avc = 0.001 * self.dataframes['General'].loc[self.index, 'AVC'].values[0]
        df_segmental = pd.DataFrame(index=self.index)

        for i, trace in enumerate(self.STRAIN_TABLES):
            df = self.dataframes[trace]
            indexes = df.index.values
            avc_view = df.index[np.argmin(np.abs(df.index.values - avc))]  # find frame closest to avc
            df.loc['strain_avc'] = df.loc[avc_view].values
            for col in df.columns:
                df.loc['ttp', col] = df[col].idxmin(axis=1)
                df.loc['ttp_ratio', col] = df.loc['ttp', col] / np.max(indexes)
                df.loc['psi', col] = np.abs((df[col].min() - df.loc['strain_avc', col])/df[col].min())
            df.loc['strain_min'] = df.min()
            df.loc['postsys'] = df.loc['ttp'] > avc_view
            df.loc['postsys'] = df.loc['postsys'].astype(bool)

            df_seg_descriptors = df.iloc[-6:, :]
            df_seg_descriptors = self._flatten_df(df_seg_descriptors)

            df_segmental = df_segmental.merge(df_seg_descriptors, left_index=True, right_index=True)
            df_segmental = df_segmental.sort_index(axis=1)

        self.dataframes['Strain Descriptors'] = df_segmental

    # -----END-StrainDescriptors----------------------------------------------------------------------------------------

    def _flatten_df(self, _df):

        _df = _df.stack().to_frame().T
        _df.columns = ["_".join(v) for v in _df.columns]
        _df = _df.set_index(self.index)
        return _df

    def _calculate_average_frame_rate(self):

        averages = np.zeros(3)
        for i, trace in enumerate(self.STRAIN_TABLES):
            averages[i] = int(np.round(1 / np.mean(np.diff(self.dataframes[trace].index.values))))

        frame_rates = pd.DataFrame(data=averages.reshape((1, 3)), index=self.index,
                                   columns=['avg_2CH_strain_fr', 'avg_4CH_strain_fr', 'avg_APLAX_strain_fr'])
        self.dataframes['Average Frame Rates'] = frame_rates

    def combine_dataframes(self):

        self._parse_all_tables()
        print('Parsing case {}'.format(self.index))
        self._calculate_average_frame_rate()
        self._find_strain_descriptors()
        self._get_gls_ge()

        all_tables = self.dataframes['General']
        for df in ['Segments', 'Average Frame Rates', 'Strain Descriptors', 'Global Descriptors']:
            all_tables = all_tables.merge(self.dataframes[df], left_index=True, right_index=True)

        # It is easier to work with the dataframe with index provided inside the file, however the labels are assigned
        # to the file names, hence change in the index:
        all_tables.rename(index={self.index[0]: basename(self.xml_file).split('.')[0]}, inplace=True)

        return all_tables
