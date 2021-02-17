import time
import logging
import base64
import json
import itertools
import gspread
import os
import sys
import importlib
import pandas as pd
from pprint import pprint
from oauth2client.service_account import ServiceAccountCredentials


class SpreadSheetDB():
    """This class makes spreadsheet as easy to use as DB.

    Getting Started
    
    1. Create SpreadSheet
    2. Create Sheet
    3. Enter Columns at First row like this:
        index	name	phone_number	email

    Parameters
    ----------
    auth_json: dict
        Google Service Accounts Private Key JSON

    spreadsheet_id: str
        SpreadSheet ID to use as DB
        in following url, the spreadsheet_id is 1c503dSOl7quggZUIV1oCJgGzR8Vz-jfzH5t59bxZXsE
        `https://docs.google.com/spreadsheets/d/1c503dSOl7quggZUIV1oCJgGzR8Vz-jfzH5t59bxZXsE/edit?usp=sharing`

    sheet_name: str
        Sheet Name to use as Table

    unique_columns: list
        INPUT a list of column names to give the UNIQUE option. Duplicate values are not entered for the UNIQUE column.

    Examples
    --------
    sdb = SpreadSheetDB(auth_json, "1c503dSOl7quggZUIV1oCJgGzR8Vz-jfzH5t59bxZXsE", "Sheet1", ["email"])
    """
    
    def __init__(self, auth_json: dict, spreadsheet_id: str, sheet_name: str, unique_columns: str = []):


        self.table = None

        self._spread_order = list(self._allcombinations(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ', minlen=1, maxlen=3))
        self._doc = self._get_doc(auth_json, spreadsheet_id)
        self._sheet_name = sheet_name
        self._cloudsheet = None
        self._index_pointer = -1
        self._unique_columns = unique_columns

        self._load()

    def insert(self, data: dict):
        """Use this function to insert data into the table.
        
        Parameters
        ----------
        data: dict
            the dict key is column name and the dict value is value. use like this.
            { "name": "Lee" }
        
        Examples
        --------
        >>> # This code insert data to the table.
        >>> sdb.insert({"name": "Park", "phone_number": "01022223333", "email": "Park@google.com"})

        """

        self._validate(data)
        self._check_unique(data)

        data["index"] = str(self._index_pointer)
        self._index_pointer += 1
        append_data = []

        for column_name in self.table.columns:
            if column_name in data:
                value = data[column_name]
            else:
                value = ""

            append_data.append(value)

        append_index = len(self.table)

        processed_append_data = []
        for value in append_data:
            value = self._convert_to_str(value)
            processed_append_data.append(value)

        self.table.loc[append_index] = processed_append_data
        self._cloudsheet.append_row(
            self._make_sheet_row(processed_append_data))

        return append_index

    def select(self, condition: pd.core.frame.DataFrame = None, columns: list = [], orient: str = "records"):
        """Use this function to get data from a table.

        Parameters
        ----------
        condition: pandas.core.frame.DataFrame
            You can use pandas dataframe indexing like this (sdb is an instnace of this class.):
            sdb.table["name"] == "Park"

        columns: list
            If you want to select all columns, leave it blank.

        orient: str
            Between `records` or `list`, You can select the shape of the output value.

        Examples
        --------
        >>> sdb.select(sdb.table["name"].isin(["Park", "Lee"]), ["name", "email"])
        [{'name': 'Park', 'email': 'Park@google.com'}, {'name': 'Lee', 'email': 'Lee@google.com'}]

        >>> sdb.select(sdb.table["name"] == "Park")
        [{'index': '34', 'name': 'Park', 'phone_number': '01022223333', 'email': 'Park@google.com'}]

        >>> sdb.select(orient="list")
        {'index': ['34', '35', '36'], 'name': ['Park', 'Lee', 'Han'],
         'phone_number': ['01022223333', '01055556666', '01077778888'],
         'email': ['Park@google.com', 'Lee@google.com', 'Han@google.com']}

        """

        t = self.table

        if condition is not None:
            t = self.table[condition]

        if len(columns):
            t = t[columns]

        return self._parse_list(orient, t.to_dict(orient))


    def update(self, condition: pd.core.frame.DataFrame, data: dict):
        """Use this function to update table.

        Parameters
        ----------
        condition: pandas.core.frame.DataFrame
            You can use pandas dataframe indexing like this (sdb is an instnace of this class.):
            sdb.table["name"] == "Park"

        data: dict
            the dict key is column name and the dict value is value. use like this.
            { "name": "Lee" }

        Examples
        --------
        >>> # This code finds the rows where the `name` column is `Park` and replace `name` with `Lee`.
        >>> sdb.update(sdb.table["name"] == "Park", { "name" : "Lee" })

        """

        self._validate(data)
        self._check_unique(data, condition)

        for key in data:
            value = data[key]
            self.table.loc[condition, key] = self._convert_to_str(value)

        selected_table = self.table[condition]
        batch_update_data = []
        eng_index = self._spread_order[len(self.table.columns) - 1]

        for index, row in selected_table.iterrows():
            values = self._make_sheet_row(row)
            spread_index = index + 2
            update_data = {
                "range": f"A{spread_index}:{eng_index}{spread_index}",
                "values": [values]
            }
            batch_update_data.append(update_data)
            self._cloudsheet.update(
                update_data["range"], update_data["values"])

        return selected_table

    def upsert(self, condition: pd.core.frame.DataFrame, data: dict):
        """Use this function to upsert table. Update if condition exists else insert data.
        
        Parameters
        ----------
        condition: pandas.core.frame.DataFrame
            You can use pandas dataframe indexing like this (sdb is an instnace of this class.):
            sdb.table["name"] == "Park"

        data: dict
            the dict key is column name and the dict value is value. use like this.
            { "name": "Lee" }        

        Examples
        --------
        >>> # This code finds the rows where the `name` column is `Park`, replace `name` with `Lee` if condition exists else insert data.
        >>> sdb.upsert(sdb.table["name"] == "Park", { "name" : "Lee" })

        """
        if len(self.select(condition)) == 0:
            return self.insert(data)
        else:
            return self.update(condition, data)

    def delete(self, condition: pd.core.frame.DataFrame) -> list:
        """Use this function to delete rows from the table.
        
        Parameters
        ----------
        condition: pandas.core.frame.DataFrame
            You can use pandas dataframe indexing like this (sdb is an instnace of this class.):
            sdb.table["name"] == "Park"

        Examples
        --------
        >>> # This code finds the rows where the `name` column is `Park` and deletes the rows.
        >>> sdb.delete(sdb.table["name"] == "Park")

        """
        
        drop_index = self.table[condition].index

        for count, index in enumerate(drop_index):
            delete_index = index + 2 - count
            self._cloudsheet.delete_row(delete_index)

        self.table = self.table.drop(
            self.table.index[drop_index]).reset_index(drop=True)

        return list(drop_index)

    def _allcombinations(self, alphabet, minlen=1, maxlen=None):
        thislen = minlen
        while maxlen is None or thislen <= maxlen:
            for prod in itertools.product(alphabet, repeat=thislen):
                yield ''.join(prod)
            thislen += 1

    def _get_doc(self, auth_json, spreadsheet_id):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://spreadsheets.google.com/feeds',
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            auth_json, scopes)
        gc = gspread.authorize(credentials)
        spreadsheet_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=0'
        doc = gc.open_by_url(spreadsheet_url)

        return doc

    def _load(self):

        self._cloudsheet = self._doc.worksheet(self._sheet_name)
        records = self._cloudsheet.get_all_values()
        rows = []
        for row in records[1:]:
            temp = []
            for p in row:
                v = self._parse(p)
                temp.append(v)

            rows.append(temp)

        self.table = pd.DataFrame(rows, columns=records[0])

        if "index" not in self.table.columns:
            raise ValueError(f"[{self._sheet_name}] Please make index column.")

        if len(self.table) == 0:
            self._index_pointer = 0
        else:
            self._index_pointer = int(self.table.iloc[-1]["index"]) + 1

    def _convert_to_str(self, value):
        if type(value) is list or type(value) is dict:
            v = json.dumps(value, ensure_ascii=False)
        else:
            v = str(value)

        return v

    def _parse(self, value):
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

    def _parse_list(self, orient, items):
        if orient == "list":
            result = {}
            for key in items:
                result[key] = []
                for item in items[key]:
                    result[key].append(self._parse(item))

        elif orient == "records":
            result = []
            for item in items:
                temp = {}
                for key in item:
                    temp[key] = self._parse(item[key])
                result.append(temp)
        else:
            raise ValueError(f"Unsupported orient {orient}")

        return result

    def _validate(self, data):

        if "index" in data:
            raise ValueError("index column is not be available to users.")

        for key in data:
            if key not in self.table.columns:
                raise ValueError(
                    f"[{key}] is not in columns. columns is {self.table.columns}")

        

    def _make_sheet_row(self, row):
        temp = []
        for p in row:
            v = self._convert_to_str(p)

            temp.append(v)

        return temp

    def _check_unique(self, data, condition=None):
        for column_name in self.table.columns:
            if column_name in data:
                value = data[column_name]
            else:
                value = ""

            if column_name in self._unique_columns:
                matchs = self.table[self.table[column_name] == value]
                if condition is None:
                    match_length = len(matchs)
                else:
                    match_length = len(
                        list(set(list(matchs.index)) - set(list(self.table[condition].index))))
                if match_length > 0:
                    raise ValueError(
                        f"{column_name} is unique, {value} already exists.")
