# Pickface Mapping Generator

## 1. Export WMS SKU data to input folder

## 2. Run Dependencies
import numpy as np
import pandas as pd
import gspread
import json
from google.colab import drive

## 3. Get Google Authentication
drive.mount('/content/gdrive')

credentials = {
  "type": "",
  "project_id": "",
  "private_key_id": "",
  "private_key": "",
  "client_email": "",
  "client_id": "",
  "auth_uri": "",
  "token_uri": "",
  "auth_provider_x509_cert_url": "",
  "client_x509_cert_url": ""
}

gc = gspread.service_account_from_dict(credentials)

## 4. Set folder paths and site-line mapping

# Set path and concats
folder_path = '/content/gdrive/Shareddrives/AutoSO/'

pfo_prefix = 'pfo_output_l'
wms_prefix = 'wms_'
lines = []
csv_suffix = '.csv'
gsheet_suffix = '.gsheet'

# Import /static/site_config.json
with open(folder_path + 'static/site_config.json') as json_file:
    site_config = json.load(json_file)

## 5. Input Menu Week

# Capture the user-inputted menu week as a string and store in variable for use throughout
print('Insert menu week in the format 000 below:')
menu_week = str(input())

## 6. Import CSVs into dictionary

# Copy site_config to new dictionary 
import_data = site_config

# Loop over each factory in the site_config.json and do:
for factory in import_data['factories']:

    # Import wms csv into factory dictionary as dataframe
    import_data['factories'][factory]['skus'] = \
    pd.read_csv(folder_path + 'input/' + menu_week + '/' + wms_prefix + factory + csv_suffix, encoding='ISO-8859-1')
    import_data['factories'][factory]['skus'].fillna('', inplace=True)

    # Rename skus column headers
    import_data['factories'][factory]['skus'].columns = \
    ['sku_id','description','group','tray_size']

    # Loop through all lines of each factory in the site_config.json and do:
    for line in import_data['factories'][factory]['lines']:
        
        # Import pfo csv into line dictionary as dataframe
        import_data['factories'][factory]['lines'][line]['pfo'] = \
        pd.read_csv(folder_path + 'input/' + menu_week + '/' + pfo_prefix + line + csv_suffix)
                

        # Rename pfo column headers
        import_data['factories'][factory]['lines'][line]['pfo'].columns = \
        ['station_name','sku_id','picks','pickslot_id']

## 7. Create Gsheets From Templates and export data in

# Loop over each factory in the site_config.json and do:
for factory in import_data['factories']:
   
    # Loop through all lines of each factory in the site_config.json and do:
    for line in import_data['factories'][factory]['lines']:
        
        # Find templates in Gdrive and import id's to dictionary
        import_data['factories'][factory]['lines'][line]['template_id'] = gc.open('so_template_l' + line).id
        
        # Create new copies from existing templates
        gc.copy(import_data['factories'][factory]['lines'][line]['template_id'], title='M' + menu_week + ' Station Ownership L' + line, copy_permissions=True)

        # Copy new SO id's back to dictionary
        import_data['factories'][factory]['lines'][line]['created_id'] = gc.open('M' + menu_week + ' Station Ownership L' + line).id

        # Open Google Sheet file
        working = gc.open_by_key(import_data['factories'][factory]['lines'][line]['created_id'])

        # WMS SKU sheet - Columns A:D - Insert skus
        worksheet = working.worksheet("WMS SKU")
        worksheet.update([import_data['factories'][factory]['skus'].columns.values.tolist()] \
                + import_data['factories'][factory]['skus'].values.tolist())

        # WMS SKU Sheet - Cell H4 - Insert menu_week
        worksheet.update('H4',menu_week)

        # Peas DS Sheet - Cell A2 - Insert pfo_data
        worksheet = working.worksheet("Peas - DS")
        worksheet.update([import_data['factories'][factory]['lines'][line]['pfo'].columns.values.tolist()] \
                + import_data['factories'][factory]['lines'][line]['pfo'].values.tolist())

drive.flush_and_unmount()