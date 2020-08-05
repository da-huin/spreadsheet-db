<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="./static/icon.png" alt="Project logo" ></a>
 <br>

 
</p>

<h3 align="center">Spreadsheet DB</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![GitHub Issues](https://img.shields.io/github/issues/dahuins/spreadsheet_db.svg)](https://github.com/kylelobo/The-Documentation-Compendium/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/dahuins/spreadsheet_db.svg)](https://github.com/kylelobo/The-Documentation-Compendium/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> This package helps you use Spreadsheet as DB in python.
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Deployment](#deployment)
- [Usage](#usage)
- [Built Using](#built_using)
- [TODO](../TODO.md)
- [Contributing](../CONTRIBUTING.md)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>

This package helps you use Spreadsheet as DB for developers.

## 🏁 Getting Started <a name = "getting_started"></a>

### Installing

```
pip install spreadsheet_db
```

<a name="prerequisites"></a>

### Prerequisites 

<a name="auth_json"></a>


#### 🌱 (Required) Download Spreadsheet Authentication JSON

1. From [Google Cloud Platform Console](https://console.developers.google.com/project), `create project` or `select an existing project`.

1. Enable [Google Drive API](https://console.developers.google.com/apis/api/drive/overview), if is not already enabled.

1. Enable [Google Sheet API](https://console.developers.google.com/apis/api/sheets.googleapis.com/overview), if is not already enabled.

1. From [Google Credential](https://console.developers.google.com/apis/api/iamcredentials.googleapis.com/credentials) choose `Create credentials` > `Service Account`.

    ![credentials_service_account](./static/credentials_service_account.png)

1. Fill out the form and click `Create Key`

    ![credentials_service_account_form](./static/credentials_service_account_form.png)

1. Click the `account you just created`, from the `Service Accounts list`.

1. click the `ADD KEY` > `Create new key`

    ![credential_create_new_key](./static/credential_create_new_key.png)

1. Set the `Key type` to JSON and click `CREATE` button

    ![credential_create_new_key_create](./static/credential_create_new_key_create.png)

1. The JSON file automatically saved, which is used to authenticate the spreadsheet.

    ![private_key_saved](./static/private_key_saved.png)


#### 🌱 (Required) Creating an Instance

`Authentication JSON` is required to create an `instance`. If you have not downloaded the `Authentication JSON`, refer to [here](#auth_json).

1. Create new [Spreadsheet](https://docs.google.com/spreadsheets/u/0/).

    ![new_spreadsheet](./static/new_spreadsheet.png)
    

1. Add `Column Names` and remember `Spreadsheet ID`.

    ![spreadsheet_column_and_id](./static/spreadsheet_column_and_id.png)

1. Change `Sheet1` to the name you want to use. in this package, uses `Sheet` as `Table`. if you want, create a new table.

    ![sheet_table](./static/sheet_table.png)

1. Create an instance using an code below.

    ```python

    import spreadsheet_db

    with open("your_auth_json_file_name.json") as fp:
        auth_json = fp.read()

    sheet_id = "Your Spreadsheet ID"
    sheet_name= "Your Sheet Name"

    # INPUT a list of column names to give the UNIQUE option. Duplicate values are not entered for the UNIQUE column.
    unique_columns = ["Column Name to use UNIQUE"]

    sdb = spreadsheet_db.SpreadSheetDB(
        auth_json, sheet_id, sheet_name, unique_columns=unique_columns)

    ```

1. From now on, you can use the spreadsheet as a DB 🎉

## 🎈 Usage <a name="usage"></a>

Please check [Prerequisites](#prerequisites) before starting `Usage`.

### 🌱 SELECT
    
Use this function to get data from a table.

**Parameters**

* `condition`: pandas.core.frame.DataFrame

    You can use pandas dataframe indexing like this (sdb is an instnace of this class.):

    ```
    sdb.table["name"] == "Park"
    ```

* `columns`: list

    If you want to select all columns, leave it blank.

* `orient`: str

    Between `records` or `list`, You can select the shape of the output value.

**Examples**

1. example 1
    ```
    >>> sdb.select(sdb.table["name"].isin(["Park", "Lee"]), ["name", "email"])
    [{'name': 'Park', 'email': 'Park@google.com'}, {'name': 'Lee', 'email': 'Lee@google.com'}]
    ```

1. example 2

    ```
    >>> sdb.select(sdb.table["name"] == "Park")
    [{'index': '34', 'name': 'Park', 'phone_number': '01022223333', 'email': 'Park@google.com'}]
    ```

1. example 3

    ```
    >>> sdb.select(orient="list")
    {'index': ['34', '35', '36'], 'name': ['Park', 'Lee', 'Han'], 'phone_number': ['01022223333', '01055556666', '01077778888'], 'email': ['Park@google.com', 'Lee@google.com', 'Han@google.com']}
    ```

### 🌱 INSERT

Use this function to insert data into the table.

**Parameters**

* `data`: dict

    the dict key is column name and the dict value is value. use like this.

    ```
    { "name": "Lee" }
    ```

**Examples**

* This code insert data to the table.

    ```
    >>> sdb.insert({"name": "Park", "phone_number": "01022223333", "email": "Park@google.com"})
    ```

### 🌱 UPDATE

Use this function to update table.

**Parameters**

* `condition`: pandas.core.frame.DataFrame

    You can use pandas dataframe indexing like this (sdb is an instnace of this class.):

    ```
    sdb.table["name"] == "Park"
    ```

* `data`: dict

    the dict key is column name and the dict value is value. use like this.

    ```
    { "name": "Lee" }
    ```

**Examples**

* This code finds the rows where the `name` column is `Park` and replace `name` with `Lee`.

    ```
    >>> sdb.update(sdb.table["name"] == "Park", { "name" : "Lee" })
    ```


### 🌱 UPSERT

Use this function to upsert table. Update if condition exists else insert data.

**Parameters**

* `condition`: pandas.core.frame.DataFrame
    You can use pandas dataframe indexing like this (sdb is an instnace of this class.):

    ```
    sdb.table["name"] == "Park"
    ```

* `data`: dict
    the dict key is column name and the dict value is value. use like this.

    ```
    { "name": "Lee" }        
    ```

**Examples**

* This code finds the rows where the `name` column is `Park`, replace `name` with `Lee` if condition exists else insert data.

    ```
    >>> sdb.upsert(sdb.table["name"] == "Park", { "name" : "Lee" })
    ```

### 🌱 DELETE

Use this function to delete rows from the table.

**Parameters**

* `condition`: pandas.core.frame.DataFrame

    You can use pandas dataframe indexing like this (sdb is an instnace of this class.):
    
    ```
    sdb.table["name"] == "Park"
    ```

**Examples**

* This code finds the rows where the `name` column is `Park` and deletes the rows.

    ```
    >>> sdb.delete(sdb.table["name"] == "Park")
    ```

## 🎉 Acknowledgements <a name = "acknowledgement"></a>

- Title icon made by [Freepik](https://www.flaticon.com/kr/authors/freepik).

- Please help develop this project 😀

- Thanks for reading 😄



