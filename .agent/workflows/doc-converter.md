---
description: create document converter
---

Implement feature convert All microsoft office file(word, excel, powerpoint) to PDF file for for this cli.
1. Implement on cli mode, read input folder and write result files to output folder(default) can pass input and output dir in cli parameter. Support multi file
2. Have a logs folder, implement best practice for logs on prefer:https://www.dash0.com/guides/logging-in-python. have both console logs and file logs. Create mordernlize log UI in console. Have progress bar file converter/total file and ETA remaining time. Create a space to write stream logs, Support write logs for multi threads process files.
3. Support 2 platform. In windows using Office 365 to prinpt file, in linux using LibreOffice to read office file and print to pdf. In windows must using COM to open office 365 for safe threads and support parrallel parse multi file(configuration)
4. In file is word(doc,docx) and powerpoint(ppt, pptx), just export to pdf keep all formant and encoding, support multi encoding for lang as eng, japanese, vietnamese.
5. In excel doing multi step as below:
- If input file is xlm or xlsm, convert it to excel and save in tmp folder. when parse pdf use this file to parse pdf
- Make sure format and layout of excel file not change anything swhen parse to excel file
- Implement all print option like
  # Page break controls - automatically split content into multiple pages
  rows_per_page: null       # Add horizontal page break every N rows (null = no automatic row breaks). Example: 50 = new page every 50 rows
  columns_per_page: null    # Add vertical page break every N columns (null = no automatic column breaks). Example: 10 = new page every 10 columns
  Make sure in this option auto break page if not fullfull data in page.
  
  scaling: "fit_columns"    # Preserve original Excel layout Options: no_scaling, fit_sheet, fit_columns, fit_rows, custom
  scaling_percent: 100 
  # Margin options (same as Excel's print margins)
  # Options: normal, wide, narrow, custom
  margins: "normal"         # Default: normal margins
  # Header/Footer options
  print_header_footer: true     # Enable/disable header and footer with sheet name and row range of current page match to excel sheet
  # Row and Column Headings (Excel row numbers on left, column letters on top)
  print_row_col_headings: false # Print Excel row numbers (1,2,3...) and column letters (A,B,C...)
- Automatic calculate width of pdf page each excel sheet base on actual size of cell value in column when scaling is fit_columns. Make sure the page size can read normaly in screen 24 inch, 1080p. And easy for OCR to detach data.
- Implemnt config.yml for all below config for dynamic each input type
- Supports multiple configurations - list format applies different settings to different sheets
  Priority: Lower number = higher priority (1 is highest). When sheet matches multiple configs, highest priority wins
  sheets: List of sheet names to apply this config to. If omitted or null, applies to all unmatched sheets (default config)
  Modes: one_page, screen_optimized
6. Output file will write to output folder(default) or from cli param. keep all folder structure as input file for folder and subfolder of file
7. Add suffix for pdf file as word (_d), excel(_x_, powerpoint(_p). it can change on config.yaml file
8. Support parallel or multi process for work to increase performance parse file.
9. Timeout convert each file is 30 min(configuration)
10 Add logging config:
   LogLevel
   LogDir
   log_console_lines: 20.