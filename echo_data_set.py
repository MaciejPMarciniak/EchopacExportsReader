import glob
import os
import pandas as pd
import numpy as np
from xml_converter import XmlConverter
from single_view_strain_reader import SingleViewStrainReader
from pathlib import Path
from sklearn.preprocessing import StandardScaler


class EchoDataSet:

    SEGMENT_NAMES = ['Basal Inferior', 'Basal Posterior', 'Basal Lateral', 'Basal Anterior', 'Basal Anteroseptal',
                     'Basal Septal', 'Mid Inferior', 'Mid Posterior', 'Mid Lateral', 'Mid Anterior', 'Mid Anteroseptal',
                     'Mid Septal', 'Apical Inferior', 'Apical Posterior', 'Apical Lateral', 'Apical Anterior',
                     'Apical Anteroseptal', 'Apical Septal']

    def __init__(self, input_path='data', output_path='data', output='all_cases.csv', file_type='xml',
                 timings_file=None):
        self.input_path = input_path
        self.output_path = self._check_directory(output_path)
        self.output = output
        if timings_file is not None:
            self.timings_file = os.path.join(self.input_path, timings_file)
        self.files = glob.glob(os.path.join(self.input_path, '*.' + file_type))
        self.files.sort()
        self.df_all_cases = None
        self.df_labels = None

    @staticmethod
    def _check_directory(directory):
        if not os.path.isdir(directory):
            os.mkdir(directory)
        return directory

    def _save_combined_dataset(self):

        output_xlsx = self.output.split('.')[0] + '.xlsx'
        output_csv = self.output.split('.')[0] + '.csv'
        self.df_all_cases.to_csv(os.path.join(self.output_path, output_csv))
        self.df_all_cases.to_excel(os.path.join(self.output_path, output_xlsx))

    def _get_all_cases_data_frame(self):

        df_filename = os.path.join(self.output_path, self.output)
        if os.path.isfile(df_filename):
            self.df_all_cases = pd.read_csv(df_filename, index_col='ID')
        else:
            try:
                self.build_data_set_from_xml_files()
            except AttributeError:
                self.build_data_set_from_txt_files()

    def find_representatives(self, features=('MW', 'strain_avc', 'strain_min')):

        self.df_labels = pd.read_excel(os.path.join(self.input_path, 'List of BSH patients_190_MM.xlsx'), index_col='ID')
        self._get_all_cases_data_frame()
        df_labelled = self.df_all_cases.join(self.df_labels['BSH'])
        df_labelled.to_excel(os.path.join(self.output_path, 'Labelled.xlsx'))

        representatives = {}
        for feature in features:
            feature_unique = feature + '_'
            feature_representatives = {}

            for i in df_labelled.BSH.unique():
                group = df_labelled[df_labelled.BSH == i]
                relevant_cols = group[[col for col in group.columns.values if feature_unique in col]]
                sc = StandardScaler()
                scaled_cols = sc.fit_transform(relevant_cols)
                relevant_cols_scaled = pd.DataFrame(scaled_cols, columns=relevant_cols.columns)
                relevant_cols_scaled['sum_col'] = relevant_cols_scaled.sum(axis=1)
                feature_representatives[i] = relevant_cols.iloc[np.abs(relevant_cols_scaled['sum_col']).idxmin(), :].name

            representatives[feature] = feature_representatives

        print(representatives['MW'])
        print(representatives['strain_avc'])
        print(representatives['strain_min'])

    def build_data_set_from_xml_files(self):

        list_of_dfs = []
        for xml_file_ in self.files:
            csv_file_ = xml_file_.split('.')[0] + '.csv'
            conv = XmlConverter(xml_file_, csv_file_)
            conv.xml2rawcsv()
            conv.build_separate_tables()

            list_of_dfs.append(conv.combine_dataframes())
            # conv.save_global_longitudinal_strains(gls_path=self.output_path)
        self.df_all_cases = pd.concat(list_of_dfs)

        self._save_combined_dataset()

    def build_data_set_from_txt_files(self):

        list_of_dfs = []
        for txt_file in self.files:
            data_set = SingleViewStrainReader(txt_file, self.timings_file)

            list_of_dfs.append(data_set.combine_dataframes())
            self.df_all_cases = pd.concat(list_of_dfs)
            data_set.save_global_longitudinal_strains(gls_path=os.path.join(self.output_path, 'gls'))

        self._save_combined_dataset()


if __name__ == '__main__':

    path_to_data = os.path.join(str(Path.home()), 'Python', 'data', 'parsing_xml', 'data')
    path_to_output = os.path.join(str(Path.home()), 'Python', 'data', 'parsing_xml', 'output')
    _timings_file = 'AVC timings for the LV 4C.xlsx'

    cases = EchoDataSet(path_to_data, output_path=path_to_output, output='all_cases.csv', file_type='xml')
    # cases.build_data_set_from_xml_files()
    # cases._read_data_frame()
    cases.find_representatives()