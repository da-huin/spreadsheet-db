import time
import logging
import base64
import json
import itertools
import gspread
import os
import os
import sys
import importlib
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

class SpreadSheetDB():

    def __init__(self, doc, worksheet_name, options={}):
        self._spread_order = list(self.allcombinations(
            'ABCDEFGHIJKLMNOPQRSTVWXYZ', minlen=1, maxlen=2))
        self.doc = doc
        self._worksheet_name = worksheet_name
        self.cloudsheet = None
        self.df = None
        self.index_pointer = -1
        self.unique_columns = []

        for key in options:
            if key == "unique_columns":
                self.unique_columns = options[key]
            else:
                raise ValueError(f"invalid options key -> {key}") 

        self.reload()

    def allcombinations(self, alphabet, minlen=1, maxlen=None):
        thislen = minlen
        while maxlen is None or thislen <= maxlen:
            for prod in itertools.product(alphabet, repeat=thislen):
                yield ''.join(prod)
            thislen += 1

    @staticmethod
    def get_doc(auth_json, spreadsheet_id):
        scope = [
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            auth_json, scope)
        gc = gspread.authorize(credentials)
        spreadsheet_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=0'
        doc = gc.open_by_url(spreadsheet_url)

        return doc

    def reload(self):
        logging.warning(f"SPREADSHEET RELOAD")

        self.cloudsheet = self.doc.worksheet(self._worksheet_name)
        records = self.cloudsheet.get_all_values()
        rows = []
        for row in records[1:]:
            temp = []
            for p in row:
                v = self.load_valid_value(p)
                temp.append(v)

            rows.append(temp)

        self.df = pd.DataFrame(rows, columns=records[0])
        
        if "index" in self.df.columns:
                
            if len(self.df) == 0:
                self.index_pointer = 0
            else:
                self.index_pointer = int(self.df.iloc[-1]["index"]) + 1
        else:
            logging.warning(f"[{self._worksheet_name}] If there is no index column, you can select only.")

    def get_valid_value(self, value):
        if type(value) is list or type(value) is dict:
            v = json.dumps(value, ensure_ascii=False)
        else:
            v = str(value)

        return v

    def load_valid_value(self, value):
        try:
            if type(value) is list or type(value) is dict:
                v = value
            elif len(value) != 0 and (value[0] == "{" or value[0] == "["):
                v = json.loads(value)
            else:
                v = str(value)
        except:
            v = str(value)

        return v

    def get_valid_dict_list(self, orient, items):
        if orient == "list":
            result = {}
            for key in items:
                result[key] = []
                for item in items[key]:
                    result[key].append(self.load_valid_value(item))


        elif orient == "records":
            result = []
            for item in items:
                temp = {}
                for key in item:
                    temp[key] = self.load_valid_value(item[key])
                result.append(temp)
        else:
            raise ValueError(f"Unsupported orient {orient}")
        # with open("items.json", "w", encoding="utf-8") as fp:
        #     fp.write(json.dumps(items, ensure_ascii=False))

        # with open("temp.json", "w", encoding="utf-8") as fp:
        #     fp.write(json.dumps(result, ensure_ascii=False))
        return result

    def select(self, condition=None, columns=[], orient="records", update=False):
        if update:
            self.reload()

        if condition is None:
            if len(columns) == 0:
                return self.get_valid_dict_list(orient, self.df.to_dict(orient))
            else:
                return self.get_valid_dict_list(orient, self.df[columns].to_dict(orient))
        if len(columns) == 0:
            return self.get_valid_dict_list(orient, self.df[condition].to_dict(orient))
        else:
            return self.get_valid_dict_list(orient, self.df[condition][columns].to_dict(orient))

    def valid_check_key_value(self, key_values):
        for key in key_values:
            if key not in self.df.columns:
                raise ValueError(
                    f"[{key}] is not in columns. columns is {self.df.columns}")


    def make_sheet_row(self, row):
        temp = []
        for p in row:
            v = self.get_valid_value(p)

            temp.append(v)


        return temp

    def update(self, condition, key_values):
        logging.warning(f"SPREADSHEET UPDATE. {key_values}")
        self.valid_check_key_value(key_values)
        self.check_unique(key_values, condition)

        for key in key_values:
            value = key_values[key]
            self.df.loc[condition, key] = self.get_valid_value(value)

        logging.warning(self.df)
        selected_df = self.df[condition]
        batch_update_data = []
        eng_index = self._spread_order[len(self.df.columns) - 1]

        for index, row in selected_df.iterrows():
            values = self.make_sheet_row(row)
            spread_index = index + 2
            update_data = {
                "range": f"A{spread_index}:{eng_index}{spread_index}",
                "values": [values]
            }
            batch_update_data.append(update_data)
            self.cloudsheet.update(update_data["range"], update_data["values"])

        return selected_df

    def upsert(self, condition, key_values):
        logging.warning(f"SPREADSHEET UPSERT. {key_values}")
        if len(self.select(condition)) == 0:
            return self.insert(key_values)
        else:
            return self.update(condition, key_values)


    def delete(self, condition):
        drop_index = self.df[condition].index

        for count, index in enumerate(drop_index):
            delete_index = index + 2 - count
            self.cloudsheet.delete_row(delete_index)

        self.df = self.df.drop(self.df.index[drop_index])
        return drop_index

    def check_int(self, s):
        if s[0] in ('-', '+'):
            return s[1:].isdigit()
        return s.isdigit()

    def check_unique(self, key_values, condition=None):
        for column_name in self.df.columns:
            if column_name in key_values:
                value = key_values[column_name]
            else:
                value = ""

            if column_name in self.unique_columns:
                matchs = self.df[self.df[column_name] == value]
                if condition is None:
                    match_length = len(matchs)
                else:
                    match_length = len(list(set(list(matchs.index)) - set(list(self.df[condition].index))))
                if match_length > 0:
                    raise ValueError(
                        f"{column_name} is unique, {value} already exists.")
  
    def insert(self, key_values):
        logging.warning(f"SPREADSHEET INSERT. {key_values['uid']}")

        self.valid_check_key_value(key_values)
        self.check_unique(key_values)

        key_values["index"] = str(self.index_pointer)
        self.index_pointer += 1
        append_data = []


        for column_name in self.df.columns:
            if column_name in key_values:
                value = key_values[column_name]
            else:
                value = ""

            append_data.append(value)

        append_index = len(self.df)

        processed_append_data = []
        for value in append_data:
            value = self.get_valid_value(value)
            processed_append_data.append(value)

        self.df.loc[append_index] = processed_append_data
        self.cloudsheet.append_row(self.make_sheet_row(processed_append_data))

        return append_index
