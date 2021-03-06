import glob
import os
import pandas as pd
import numpy as np
from xml_converter import XmlConverter
from single_view_strain_reader import SingleViewStrainReader
from sklearn.preprocessing import StandardScaler
from pathlib import Path


class EchoDataSet:

    SEGMENT_NAMES = ['Basal Inferior', 'Basal Posterior', 'Basal Lateral', 'Basal Anterior', 'Basal Anteroseptal',
                     'Basal Septal', 'Mid Inferior', 'Mid Posterior', 'Mid Lateral', 'Mid Anterior', 'Mid Anteroseptal',
                     'Mid Septal', 'Apical Inferior', 'Apical Posterior', 'Apical Lateral', 'Apical Anterior',
                     'Apical Anteroseptal', 'Apical Septal']

    AHA_17_SEGMENT_NAMES = ['Basal Anterior', 'Basal Anteroseptal', 'Basal Inferoseptal',
                            'Basal Inferior', 'Basal Inferolateral', 'Basal Anterolateral',
                            'Mid Anterior', 'Mid Anteroseptal', 'Mid Inferoseptal',
                            'Mid Inferior', 'Mid Inferolateral', 'Mid Anterolateral',
                            'Apical Anterior', 'Apical Septal', 'Apical Inferior', 'Apical Lateral', 'Apex']

    def __init__(self, input_path='data', output_path='data', output='all_cases.csv', export_file_type='xml',
                 timings_file=None):
        """
        Process all EchoPAC exports included in the input_path.
        :param input_path: Path to the folder with EchoPAC exports
        :param output_path: Path to a folder where resulting table will be saved
        :param output: name of the .csv and .xlsx table file
        :param export_file_type: Type of the exports:
            xml: full export with work indices calculated,
            txt: partial export - strain of only one view (4C, 3C or 2C) was exported
        :param timings_file: An additional file with aortic valve closure timings, used with single-view export to
        calculate the post-systolic index.
        """
        self.input_path = input_path
        self.output_path = self._check_directory(output_path)
        self.output = output
        if timings_file is not None:
            self.timings_file = os.path.join(self.input_path, timings_file)
        self.files = glob.glob(os.path.join(self.input_path, '*.' + export_file_type))
        self.files.sort()
        self.df_all_cases = None
        self.label_col = None

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

    def _get_group_data(self, _df, _feat, _group):

        group = _df[_df[self.label_col] == _group]
        try:
            relevant_cols = group[[col for col in group.columns.values if _feat in col]]
        except TypeError:
            relevant_cols = group[[col for col in group.columns.values for single_ft in _feat if single_ft in col]]

        return relevant_cols

    def _group_representatives(self, df, feat):

        feature_representatives = {}
        for group in df[self.label_col].unique():
            relevant_cols = self._get_group_data(df, feat, group)
            print(group)
            print(relevant_cols)

            sc = StandardScaler()
            scaled_cols = sc.fit_transform(relevant_cols)
            relevant_cols_scaled = pd.DataFrame(scaled_cols, columns=relevant_cols.columns)
            relevant_cols_scaled['sum_col'] = relevant_cols_scaled.sum(axis=1)
            feature_representatives[group] = relevant_cols.iloc[np.abs(relevant_cols_scaled['sum_col']).idxmin(), :].name
        return feature_representatives

    def _calculate_17_aha_values(self, segmental_values, echop=True):

        aha_17 = pd.DataFrame(columns=self.AHA_17_SEGMENT_NAMES)

        segmental_values.columns = [x.split('_')[-1] for x in segmental_values.columns]
        segmental_values.rename(columns={'Basal Septal': 'Basal Inferoseptal', 'Basal Posterior': 'Basal Inferolateral',
                                         'Basal Lateral': 'Basal Anterolateral', 'Mid Septal': 'Mid Inferoseptal',
                                         'Mid Posterior': 'Mid Inferolateral', 'Mid Lateral': 'Mid Anterolateral'},
                                inplace=True)

        for col in aha_17.columns:
            print(segmental_values.columns)
            if ('Basal' in col or 'Mid' in col) and col in segmental_values.columns:
                aha_17.loc['mean', col] = int(segmental_values.loc['mean', col])
                aha_17.loc['median', col] = int(segmental_values.loc['median', col])

        for val in ['mean', 'median']:
            if not echop:
                aha_17.loc[val, 'Apical Inferior'] = int((segmental_values.loc[val, 'Apical Inferior'] * 4 +
                                                          segmental_values.loc[val, 'Apical Posterior'] +
                                                          segmental_values.loc[val, 'Apical Septal']) / 6)
                aha_17.loc[val, 'Apical Anterior'] = int((segmental_values.loc[val, 'Apical Anterior'] * 4 +
                                                          segmental_values.loc[val, 'Apical Anteroseptal'] +
                                                          segmental_values.loc[val, 'Apical Lateral']) / 6)
                aha_17.loc[val, 'Apical Septal'] = int((segmental_values.loc[val, 'Apical Septal'] +
                                                        segmental_values.loc[val, 'Apical Anteroseptal']) / 2)
                aha_17.loc[val, 'Apical Lateral'] = int((segmental_values.loc[val, 'Apical Lateral'] +
                                                         segmental_values.loc[val, 'Apical Posterior']) / 2)
            else:
                aha_17.loc[val, 'Apical Inferior'] = int((segmental_values.loc[val, 'Apical Inferior'] * 2 +
                                                          segmental_values.loc[val, 'Apical Posterior']) / 3)
                aha_17.loc[val, 'Apical Anterior'] = int((segmental_values.loc[val, 'Apical Anterior'] * 2 +
                                                          segmental_values.loc[val, 'Apical Anteroseptal']) / 3)
                aha_17.loc[val, 'Apical Septal'] = int((segmental_values.loc[val, 'Apical Septal'] * 2 +
                                                        segmental_values.loc[val, 'Apical Anteroseptal']) / 3)
                aha_17.loc[val, 'Apical Lateral'] = int((segmental_values.loc[val, 'Apical Lateral'] * 2 +
                                                         segmental_values.loc[val, 'Apical Posterior']) / 3)

            aha_17.loc[val, 'Apex'] = int(segmental_values.loc[val, ['Apical Lateral', 'Apical Septal',
                                                                     'Apical Anterior', 'Apical Anteroseptal',
                                                                     'Apical Inferior', 'Apical Posterior']].sum() / 6)
        return aha_17

    def _find_mean_and_median_for_aha_plot(self, df, feat, n_segments):

        feature_plot_values = {}

        for group in df[self.label_col].unique():
            relevant_cols = self._get_group_data(df, feat, group)
            print(relevant_cols)
            relevant_cols.loc['mean'] = relevant_cols.mean()
            relevant_cols.loc['median'] = relevant_cols.median()
            if n_segments == 17:
                feature_plot_values['group_{}'.format(group)] = \
                    self._calculate_17_aha_values(relevant_cols.loc[['mean', 'median']])
            else:
                feature_plot_values['group_{}'.format(group)] = relevant_cols.loc[['mean', 'median']].astype(int)

        return feature_plot_values

    def get_aha_values(self, features=('MW', 'strain_avc', 'strain_min'), label_col='BSH', representatives=False,
                       n_segments=17, labels_file=''):
        """
        Obtain the mean and median segmental values of parameters of interest, with respect to the patient classes
        (groups).
        :param features: parameters to extract
        :param label_col: name of the column with classification of the patients
        :param representatives: whether to produce the table of class (group) representative patients
        :param n_segments: 17 or 18 - as used for creating the AHA plots
        :param labels_file: name of the file containing patient classification
        :return: either the list of group representatives or means and medians segmental values of the parameters
        of interest
        """

        if not os.path.exists(os.path.join(self.output_path, 'Labelled.xlsx')):
            self.label_col = label_col
            df_labels = pd.read_excel(os.path.join(self.input_path, labels_file), index_col='ID')
            self._get_all_cases_data_frame()
            df_labelled = self.df_all_cases.join(df_labels[self.label_col])
            df_labelled.to_excel(os.path.join(self.output_path, 'Labelled.xlsx'))
        else:
            self.label_col = label_col
            self._get_all_cases_data_frame()
            df_labelled = pd.read_excel(os.path.join(self.output_path, 'Labelled.xlsx'), index_col='ID')

        result = {}
        if representatives:
            for feature in features:
                print('feautre: {}'.format(feature))
                feature_unique = feature + '_'
                result[feature] = self._group_representatives(df_labelled, feature_unique)
            result['all'] = self._group_representatives(df_labelled, [feat + '_' for feat in features])
            df_reps = pd.DataFrame(result)
            df_reps.index.name = 'Label'
            df_reps.to_excel(os.path.join(self.output_path, 'representatives.xlsx'))
            return df_reps

        else:
            for feature in features:
                print('feature: {}'.format(feature))
                feature_unique = feature + '_'
                result[feature] = self._find_mean_and_median_for_aha_plot(df_labelled, feature_unique, n_segments)

            if n_segments == 17:
                df_all_features = pd.DataFrame(columns=self.AHA_17_SEGMENT_NAMES)
            else:
                df_all_features = pd.DataFrame(columns=self.SEGMENT_NAMES)

            for feature in features:
                for group in df_labelled[self.label_col].unique():
                    df_reps = pd.DataFrame(result[feature]['group_{}'.format(group)])
                    group = int(group) if isinstance(group, float) else group
                    if n_segments == 18:
                        df_reps.columns = [x.split('_')[-1] for x in df_reps.columns]
                    df_all_features.loc['mean_{}_{}'.format(feature, group)] = df_reps.loc['mean']
                    df_all_features.loc['median_{}_{}'.format(feature, group)] = df_reps.loc['median']

            df_all_features.dropna(axis=0, inplace=True)
            print(df_all_features)
            df_all_features.to_excel(os.path.join(self.output_path, 'population_{}_AHA.xlsx'.format(n_segments)))

            return df_all_features

    def build_data_set_from_xml_files(self):

        list_of_dfs = []
        for xml_file_ in self.files:
            csv_file_ = xml_file_.split('.')[0] + '.csv'
            conv = XmlConverter(xml_file_, csv_file_)
            conv.xml2rawcsv()
            conv.build_separate_tables()

            list_of_dfs.append(conv.combine_dataframes())
            # conv.save_global_longitudinal_strains(gls_path=self.output_path)
        self.df_all_cases = pd.concat(list_of_dfs, sort=False)

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

    path_to_data = os.path.join(str(Path.home()), 'Python', 'data', 'parsing_xml', 'MW exports ESC')
    path_to_output = os.path.join(str(Path.home()), 'Python', 'data', 'parsing_xml', 'MW exports ESC', 'output')
    _timings_file = 'AVC timings for the LV 4C v2.xlsx'

    cases = EchoDataSet(path_to_data, output_path=path_to_output, output='all_cases.csv', export_file_type='xml',
                        timings_file=_timings_file)
    # cases.build_data_set_from_txt_files()
    cases.get_aha_values(label_col='Category', n_segments=18, labels_file='MW list with categorisation.xlsx',
                         representatives=False)



