import os
import ntpath
import pandas as pd
import numpy as np
from pathlib import Path

# TODO: comment with short descriptions


class SingleViewStrainReader:

    strain_colors = ['YELLOW', 'CYAN', 'GREEN', 'MAGENTA', 'BLUE', 'RED']
    strain_columns = ['basal_inferoseptum', 'mid_inferoseptum', 'apical_inferoseptum', 'apical_anterolateral',
                      'mid_anterolateral', 'basal_anterolateral']

    def __init__(self, txt_file, timings_file):
        """
        It is possible to export a .txt file from EchoPAC with a single view (4C, 3C or 2C) strain measurements, which
        can be used for analysis.
        :param txt_file: .txt file with strain data
        :param timings_file: .xlsx file with timing of the aortic valve closure
        """
        self.txt_file = txt_file
        self.timings_file = timings_file

        self.ID = str(ntpath.basename(self.txt_file).split('.')[0])
        self.frame_rate = 0
        self.strain_table = None
        self.descriptor_table = None
        self.avc_time = 0
        self.avc_view = 0

    @staticmethod
    def _check_directory(directory):
        if not os.path.isdir(directory):
            os.mkdir(directory)
            print(directory)
        return directory

    # -----StrainDescriptors--------------------------------------------------------------------------------------------

    def _get_avc_time(self):
        df = pd.read_excel(self.timings_file, sep=',', header=0, index_col='ID')
        id = self.ID.split('_')[0]
        self.avc_time = df.loc[id, 'AVC'] / 1000.0

        return self.avc_time

    def _get_frame_rate(self):
        with open(self.txt_file, 'r') as f:
            f.readline()
            f.readline()
            info = f.readline()
            frame_rate = int(info[3:7])

            return frame_rate

    def _get_min_strains(self):
        df = self.strain_table[self.strain_columns]
        df_min = pd.DataFrame(df.min(axis='rows')).T
        df_min.columns = ['max_strain_' + col for col in df_min.columns]
        df_min.index = [self.ID]

        return df_min

    def _get_psi(self, df=pd.DataFrame()):

        df = pd.DataFrame(df)
        min_values = df.min(axis='rows')

        if not self.avc_view:
            if not self.avc_time:
                _ = self._get_avc_time()
            self.avc_view = df.index[np.argmin(np.abs(df.index.values - self.avc_time))]  # find frame closest to avc
        dict_psi = {}
        for i, mv in enumerate(min_values):
            col = df.iloc[:, i]
            if np.abs(col[col == mv].index[0] - self.avc_view) < 1e-3:
                post_systolic = 0
            elif col[col == mv].index[0] > self.avc_view:
                post_systolic = 1
            else:
                post_systolic = -1
            dict_psi[str(min_values.index[i]).lower() + '_psi'] = post_systolic

        df_psi = pd.DataFrame(dict_psi, index=[self.ID])
        df_psi = df_psi.rename(columns={'global_psi': 'gls_psi'})

        return df_psi

    def _get_segmental_strain_at_avc(self):
        df = self.strain_table[self.strain_columns]
        if not self.avc_view:
            if not self.avc_time:
                _ = self._get_avc_time()
            self.avc_view = df.index[np.argmin(np.abs(df.index.values - self.avc_time))]  # find frame closest to avc
        df_avc = pd.DataFrame(df.loc[self.avc_view]).T
        df_avc.columns = ['avc_strain_' + col for col in df_avc]
        df_avc.index = [self.ID]

        return df_avc

    def _get_gls_ge(self):
        df = self.strain_table['GLOBAL']
        df_before_avc = df.loc[:self.avc_view]
        df_before_avc.append(df.loc[[self.avc_view]])
        max_global_strain_before_avc = df_before_avc.min(axis='rows')
        max_global_strain = df.min(axis='rows')

        dict_gls = {'max_gls_before_avc': max_global_strain_before_avc, 'max_gls': max_global_strain,
                    'avc_time': self.avc_view, 'max_gls_time': df[df == max_global_strain].index[0]}
        df_gls = pd.DataFrame(dict_gls, index=[self.ID])

        return df_gls

    def _calculate_psi(self):
        df_min = self._get_min_strains()
        df_avc = self._get_segmental_strain_at_avc()

        df_psi = pd.DataFrame(index=[self.ID], columns=['psi_' + col for col in self.strain_columns])
        for i, col in enumerate(zip(df_min.columns, df_avc.columns)):
            df_psi.iloc[:, i] = (df_min[col[0]] - df_avc[col[1]]) / df_min[col[0]] * 100

        return df_psi

    # -----ENDStrainDescriptors-----------------------------------------------------------------------------------------

    # -----ReadData-----------------------------------------------------------------------------------------------------

    def _txt_to_df(self):
        print('Parsing {}'.format(self.ID))
        self.strain_table = pd.read_csv(self.txt_file, header=0, index_col=0, sep='\t',
                                        skiprows=[0, 1, 2]).dropna(axis='columns')
        self.strain_table.columns = [col.strip(' ') for col in self.strain_table.columns]
        self.strain_table = self.strain_table.rename(columns={self.strain_colors[0]: self.strain_columns[0],
                                                              self.strain_colors[1]: self.strain_columns[1],
                                                              self.strain_colors[2]: self.strain_columns[2],
                                                              self.strain_colors[3]: self.strain_columns[3],
                                                              self.strain_colors[4]: self.strain_columns[4],
                                                              self.strain_colors[5]: self.strain_columns[5]})
        # Beginning of the cycle:
        r_indexes = self.strain_table.loc[(np.abs(self.strain_table[self.strain_columns[0]]) < 1e-6) &
                                          (np.abs(self.strain_table[self.strain_columns[1]]) < 1e-6) &
                                          (np.abs(self.strain_table[self.strain_columns[2]]) < 1e-6) &
                                          (np.abs(self.strain_table[self.strain_columns[3]]) < 1e-6) &
                                          (np.abs(self.strain_table[self.strain_columns[4]]) < 1e-6) &
                                          (np.abs(self.strain_table[self.strain_columns[5]]) < 1e-6)].index
        self.strain_table = self.strain_table[self.strain_table.index >= r_indexes[0]]
        self.strain_table = self.strain_table[self.strain_table.index <= r_indexes[1]]
        self.strain_table.index = self.strain_table.index.values - r_indexes[0]

    # -----ENDReadData--------------------------------------------------------------------------------------------------

    # -----ReadingAndSaving---------------------------------------------------------------------------------------------
    def combine_dataframes(self):
        """
        :return: a data frame with relevant values from the .txt file, as well as segmental value at aortic valve
        closure, post-systolic index and global strain values.
        """
        self._txt_to_df()

        df_descriptors = pd.DataFrame(index=[self.ID])
        df_descriptors['frame_rate (FPS)'] = self._get_frame_rate()
        df_descriptors = df_descriptors.merge(self._get_segmental_strain_at_avc(), left_index=True, right_index=True)
        df_descriptors = df_descriptors.merge(self._get_min_strains(), left_index=True, right_index=True)
        df_descriptors = df_descriptors.merge(self._calculate_psi(), left_index=True, right_index=True)
        df_descriptors = df_descriptors.merge(self._get_gls_ge(), left_index=True, right_index=True)
        df_descriptors = df_descriptors.merge(self._get_psi(self.strain_table['GLOBAL']), left_index=True, right_index=True)
        df_descriptors = df_descriptors.merge(self._get_psi(self.strain_table[self.strain_columns]), left_index=True,
                                              right_index=True)
        self.descriptor_table = df_descriptors

        return df_descriptors

    def save_global_longitudinal_strains(self, gls_path=''):
        gls = self.strain_table['GLOBAL']
        gls_path = self._check_directory(gls_path)
        gls_xls_file_path = os.path.join(gls_path, str(self.ID) + '_mean_global_traces.xls')
        gls.to_excel(gls_xls_file_path)
        gls_csv_file_path = os.path.join(gls_path, str(self.ID) + '_mean_global_traces.csv')
        gls.to_csv(gls_csv_file_path, header=True)

    # -----ENDReadingAndSaving------------------------------------------------------------------------------------------


if __name__ == '__main__':

    path_to_data = os.path.join(str(Path.home()), 'Python', 'data', '4C strains')
    path_to_output = os.path.join(path_to_data, 'output')
    _timings_file = os.path.join(path_to_data, 'AVC timings for the LV 4C v2.xlsx')

    case = SingleViewStrainReader(os.path.join(path_to_data, 'ABC0455_4C.txt'), timings_file=_timings_file)
    case.combine_dataframes()
