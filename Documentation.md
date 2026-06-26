Documentation

## Table of Contents
1. Introduction
2. Features
3. Technologies Used
4. Project Structure
5. Setup and Installation
6. Usage
7. DSL Commands
8. Frontend Overview
9. Backend Overview
10. API Endpoints
11. Future Enhancements
12. Contributing
13. License

---

## 1. Introduction
The **DataScript Compiler** is a web-based application that allows users to process CSV files using a custom Domain-Specific Language (DSL). Users can upload a CSV file, write DSL commands to manipulate the data, and download the processed file. This tool is designed to simplify data transformation tasks for non-technical users while providing flexibility for advanced users.

---

## 2. Features
- Upload CSV, JSON, or Excel files for processing.
- Write and execute DSL commands to manipulate data.
- Download the processed CSV, JSON, or Excel file.
- Intuitive and responsive frontend interface.
- Backend powered by Flask for efficient data processing.

---

## 3. Technologies Used
### Frontend:
- **HTML5**: Structure of the web application.
- **CSS3**: Styling and layout.
- **JavaScript**: Client-side interactivity.

### Backend:
- **Python**: Core programming language.
- **Flask**: Web framework for handling API requests.
- **Pandas**: Data manipulation and analysis library.

---

## 4. Project Structure
```
DataScript_Compiler - v3/
│
├── backend/
│   ├── app.py                # Main Flask application
│   ├── processed/            # Folder to store processed files
│
├── frontend/
│   ├── index.html            # Main HTML file
│   ├── styles.css            # CSS file for styling
│   ├── script.js             # JavaScript file for frontend logic
│   ├── Documentation.txt     # DSL and usage documentation
│
└── README.md                 # Project documentation
```

---

## 5. Setup and Installation
### Prerequisites:
- Python 3.8 or higher
- pip (Python package manager)

### Steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/DataScript_Compiler.git
   cd DataScript_Compiler
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask application:
   ```bash
   python backend/app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

---

## 6. Usage
1. Open the application in your browser.
2. Upload a CSV file using the file input field.
3. Write DSL commands in the text area to manipulate the data.
4. Click the "Run Script" button to process the file.
5. If successful, a download link will appear to download the processed file.

---

## 7. DSL Commands
The DSL (Domain-Specific Language) now supports 50+ operations for advanced data manipulation. Below are some of the supported commands (see full list in the codebase):

- LOAD, SAVE, DROP, DROPNA, FILLNA, RENAME, DROP_DUPLICATES, UNIQUE, HEAD, TAIL, SORT, RESET_INDEX, SET_INDEX, FILTER, QUERY, DESCRIBE, INFO, SHAPE, COLUMNS, DUPLICATE_ROWS, ISNULL, NOTNULL, VALUE_COUNTS, APPLY, MAP, REPLACE, STRIP, LOWER, UPPER, CONCAT, SPLIT, MERGE, JOIN, GROUPBY, PIVOT, MELT, AGGREGATE, SUM, MEAN, MEDIAN, MIN, MAX, COUNT, STD, VAR, CUMSUM, CUMPROD, SHIFT, ROLLING, PERCENTILE, CORR, COV, SAMPLE, REINDEX, TRANSPOSE, EXPLODE

### Example Script:
```plaintext
LOAD;
DROP 'unnecessary_column';
RENAME 'old_name' TO 'new_name';
FILTER 'age > 30';
GROUPBY 'department' AGG 'sum';
SAVE 'processed_data.csv';
```

---

## 8. Frontend Overview
The frontend is designed to provide a clean and user-friendly interface for interacting with the application.

### Key Components:
1. **File Upload**: Allows users to upload a CSV file.
2. **DSL Script Editor**: A text area for writing DSL commands.
3. **Run Button**: Executes the DSL script and processes the file.
4. **Download Link**: Appears after successful processing to download the output file.

### Styling:
The frontend uses a modern design with a responsive layout. The color scheme is based on green tones (`#4CAF50`) for a professional look.

---

## 9. Backend Overview
The backend is built using Flask and handles the following tasks:
1. Serving the frontend files.
2. Processing the uploaded CSV file based on the DSL commands.
3. Returning the processed file for download.

### Key Libraries:
- **Flask**: For routing and API handling.
- **Pandas**: For data manipulation.

---

## 10. API Endpoints
### 10.1 `/` (GET)
Serves the frontend `index.html`.

### 10.2 `/run-script` (POST)
Processes the uploaded CSV file based on the DSL script.

#### Request:
- **file**: CSV file to process.
- **script**: DSL commands.

#### Response:
- On success: JSON with the filename of the processed file.
- On failure: JSON with an error message.

### 10.3 `/download/<filename>` (GET)
Allows users to download the processed file.

#### Response:
- On success: The processed file.
- On failure: JSON with an error message.

---

## 11. Future Enhancements
- Add more DSL commands for advanced data manipulation.
- Implement user authentication for secure file processing.
- Add support for other file formats (e.g., Excel).
- Provide real-time feedback for DSL script errors.
- Enhance the frontend with a live preview of the processed data.
- Add session-based script history and DSL script saving/loading.
- Add backend log download for debugging.

---

## 12. Contributing
We welcome contributions from the community! To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

---

## 13. License
This project is licensed under the MIT License. See the `LICENSE` file for details.