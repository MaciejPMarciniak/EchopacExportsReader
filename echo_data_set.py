import glob
import os
import pandas as pd
from xml_converter import XmlConverter
from single_view_strain_reader import SingleViewStrainReader
from pathlib import Path


class EchoDataSet:

    def __init__(self, path='data', output_path='data', output='all_cases.csv', file_type='xml'):
        self.path = path
        self.output_path = self._check_directory(output_path)
        self.output = output
        self.files = glob.glob(os.path.join(self.path, '*.' + file_type))
        self.files.sort()
        print(self.files)
        self.df_all_cases = None

    @staticmethod
    def _check_directory(directory):
        if not os.path.isdir(directory):
            os.mkdir(directory)
        return directory

    def build_data_set_from_xml_files(self):

        list_of_dfs = []
        for xml_file_ in self.files:
            csv_file_ = xml_file_.split('.')[0] + '.csv'
            conv = XmlConverter(xml_file_, csv_file_)
            conv.xml2rawcsv()
            conv.build_separate_tables()

            list_of_dfs.append(conv.combine_dataframes())
            conv.save_global_longitudinal_strains(gls_path=self.output_path)

        self._save_combined_dataset(list_of_dfs)

    def build_data_set_from_txt_files(self, timings='AVC timings for the LV 4C.xlsx'):

        timings_file_ = os.path.join(self.path, timings)
        list_of_dfs = []
        for txt_file in self.files:
            data_set = SingleViewStrainReader(txt_file, timings_file_)

            list_of_dfs.append(data_set.combine_dataframes())
            data_set.save_global_longitudinal_strains(gls_path=os.path.join(self.path, 'gls'))

        self._save_combined_dataset(list_of_dfs)

    def _save_combined_dataset(self, list_of_dfs):

        output_xlsx = self.output.split('.')[0] + '.xlsx'
        output_csv = self.output.split('.')[0] + '.csv'
        self.df_all_cases = pd.concat(list_of_dfs)
        self.df_all_cases.to_csv(os.path.join(self.output_path, output_csv))
        self.df_all_cases.to_excel(os.path.join(self.output_path, output_xlsx))


if __name__ == '__main__':

    path_to_data = os.path.join(str(Path.home()), 'Python', 'data', 'parsing_xml', 'Myocardial_export_n_172')
    path_to_output = os.path.join(path_to_data, 'output')
    _timings_file = 'AVC timings for the LV 4C.xlsx'

    cases = EchoDataSet(path_to_data, output_path=path_to_output, output='all_cases.csv', file_type='xml')
    cases.build_data_set_from_xml_files()
