from flask import Flask, request, send_from_directory, jsonify
import pandas as pd
import os
import logging
import math
import re
import uuid
from lexer import Lexer
from parser import Parser
from code_generator import CodeGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("backend/app.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__, static_folder="../frontend", static_url_path="/")

# Folder to store uploaded and processed files
UPLOAD_FOLDER = os.path.join("backend", "uploads")
PROCESSED_FOLDER = os.path.join("backend", "processed")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_column_key(name):
    normalized = str(name).strip().replace("\ufeff", "")
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[^0-9A-Za-z_]", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized.lower()


def normalize_dataframe_columns(df):
    rename_map = {}
    used = set()
    for original in df.columns:
        base_name = str(original).strip().replace("\ufeff", "")
        candidate = re.sub(r"\s+", "_", base_name)
        candidate = re.sub(r"[^0-9A-Za-z_]", "_", candidate)
        candidate = re.sub(r"_+", "_", candidate).strip("_") or "column"

        unique_name = candidate
        suffix = 2
        while unique_name in used:
            unique_name = f"{candidate}_{suffix}"
            suffix += 1

        used.add(unique_name)
        rename_map[original] = unique_name

    return df.rename(columns=rename_map), rename_map


def resolve_requested_columns(df, requested_columns):
    normalized_map = {normalize_column_key(column): column for column in df.columns}
    resolved = []
    missing = []

    for requested in requested_columns:
        resolved_column = normalized_map.get(normalize_column_key(requested))
        if resolved_column is None:
            missing.append(requested)
        else:
            resolved.append(resolved_column)

    if missing:
        available = ", ".join(map(str, df.columns))
        missing_display = ", ".join(missing)
        raise ValueError(f"Unknown column(s): {missing_display}. Available columns: {available}")

    return resolved


def to_dataframe(value):
    if isinstance(value, pd.DataFrame):
        return value
    if isinstance(value, pd.Series):
        series_name = value.name or "value"
        return value.reset_index(name=series_name)
    return None


def preview_records(value, limit=10):
    preview_df = to_dataframe(value)
    if preview_df is None:
        return None
    preview_df = preview_df.head(limit).copy()
    preview_df = preview_df.where(pd.notnull(preview_df), None)
    return preview_df.to_dict(orient='records')


def make_json_safe(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(key): make_json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    if hasattr(value, "tolist") and not isinstance(value, str):
        try:
            return make_json_safe(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (str, int, bool)):
        return value
    return str(value)


def build_result_payload(value):
    if value is None:
        return None
    preview = preview_records(value)
    if preview is not None:
        return {"type": "table", "preview": preview}
    return {"type": "value", "value": make_json_safe(value)}


def run_fetch_query(df, selected_columns, condition=None):
    working_df, _ = normalize_dataframe_columns(df)

    if condition:
        normalized_condition = condition
        columns_by_length = sorted(working_df.columns, key=len, reverse=True)
        for column in columns_by_length:
            normalized_condition = re.sub(
                rf"(?<![0-9A-Za-z_]){re.escape(column)}(?![0-9A-Za-z_])",
                f"`{column}`",
                normalized_condition,
            )
        try:
            working_df = working_df.query(normalized_condition, engine="python").copy()
        except Exception as exc:
            available = ", ".join(map(str, working_df.columns))
            raise ValueError(
                f"Invalid WHERE clause: {condition}. Available columns: {available}"
            ) from exc
    else:
        working_df = working_df.copy()

    if selected_columns != ["*"]:
        resolved_columns = resolve_requested_columns(working_df, selected_columns)
        working_df = working_df[resolved_columns].copy()

    return working_df

def is_balanced_parentheses(s):
    stack = []
    for c in s:
        if c == '(':
            stack.append(c)
        elif c == ')':
            if not stack:
                return False
            stack.pop()
    return not stack

# Serve Frontend
@app.route('/')
def serve_index():
    return app.send_static_file("index.html")

# DSL Processing
@app.route('/run-script', methods=['POST'])
def run_script():
    file = request.files.get('file')
    script = request.form.get('script', '').strip()
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "No valid file uploaded"}), 400

    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_id = str(uuid.uuid4())
    upload_filename = f"input_{unique_id}{file_ext}"
    upload_path = os.path.join(UPLOAD_FOLDER, upload_filename)
    file.save(upload_path)

    # Load the DataFrame
    try:
        if file_ext == '.csv':
            df = pd.read_csv(upload_path)
        elif file_ext == '.json':
            df = pd.read_json(upload_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(upload_path)
        else:
            return jsonify({"error": "Unsupported file format"}), 400
    except Exception as e:
        logging.error(f"File read error: {e}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    logging.info(f"Received DSL Script:\n{script}")

    try:
        # Compiler pipeline: Lexer -> Parser -> CodeGen -> Exec
        lexer = Lexer(script)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        commands = parser.parse()
        # Check for malformed commands before codegen
        for cmd in commands:
            if not is_balanced_parentheses(cmd):
                logging.error(f"Malformed command (unbalanced parentheses): {cmd}")
                return jsonify({"error": f"Malformed command: {cmd}"}), 400
        codegen = CodeGenerator(commands)
        code = codegen.generate_code()
        logging.info(f"Generated code:\n{code}")

        df, _ = normalize_dataframe_columns(df)

        # Prepare the execution environment
        exec_env = {'pd': pd, 'df': df, 'run_fetch_query': run_fetch_query}
        try:
            exec(code, exec_env, exec_env)
            df_result = exec_env.get('df', df)
            command_result = exec_env.get('result')
            output_fname = exec_env.get('output_filename')
        except Exception as e:
            logging.error(f"Execution error: {e}\nCode was:\n{code}")
            return jsonify({"error": f"Execution failed: {str(e)}"}), 400

        result_payload = build_result_payload(command_result)
        result_is_table = result_payload is not None and result_payload["type"] == "table"
        df_to_save = to_dataframe(df_result)
        save_target = to_dataframe(command_result) if result_is_table else df_to_save
        should_save_dataframe = save_target is not None and (
            output_fname is not None or command_result is None or result_is_table
        )
        preview = preview_records(save_target) if should_save_dataframe else None
        processed_filename = None
        if should_save_dataframe:
            requested_ext = os.path.splitext(output_fname or "")[1].lower()
            output_ext = ".json" if requested_ext == ".json" else ".csv"
            processed_filename = f"processed_{unique_id}{output_ext}"
            processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)

            try:
                if save_target.empty:
                    logging.error("Processed DataFrame is empty.")
                    return jsonify({"error": "Processed data is empty. Nothing to save."}), 400
                if output_ext == '.csv':
                    save_target.to_csv(processed_path, index=False)
                else:
                    save_target.to_json(processed_path, orient='records', lines=True)
                if not os.path.exists(processed_path):
                    logging.error(f"Processed file not found after save: {processed_path}")
                    return jsonify({"error": "Processed file could not be created."}), 500
                logging.info(f"Saved processed file: {processed_path}")
            except Exception as e:
                logging.error(f"File save error: {e}")
                return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

        message = "Processing complete" if processed_filename else "Command executed"
        return jsonify({
            "message": message,
            "filename": processed_filename,
            "preview": preview,
            "result": result_payload,
        })
    except (SyntaxError, ValueError, NotImplementedError) as e:
        logging.error(f"Processing error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Processing error: {e}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500
    finally:
        try:
            os.remove(upload_path)
        except Exception:
            pass

# Download processed file
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    if filename == "app.log":
        # Allow download of backend log
        log_path = os.path.join("backend", "app.log")
        if not os.path.exists(log_path):
            return jsonify({"error": "Log file not found"}), 404
        return send_from_directory("backend", "app.log", as_attachment=True)
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if not os.path.exists(file_path):
        logging.error(f"Download requested but file not found: {file_path}")
        return jsonify({"error": "File not found"}), 404
    try:
        return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Error sending file {filename}: {e}")
        return jsonify({"error": f"Failed to send file: {str(e)}"}), 500

@app.route('/Documentation.txt')
def serve_documentation():
    # Try backend first, then frontend
    backend_doc = os.path.join(os.path.dirname(__file__), 'Documentation.txt')
    frontend_doc = os.path.abspath(os.path.join(app.static_folder, 'Documentation.txt'))
    if os.path.exists(backend_doc):
        return send_from_directory(os.path.dirname(backend_doc), 'Documentation.txt')
    elif os.path.exists(frontend_doc):
        return send_from_directory(os.path.dirname(frontend_doc), 'Documentation.txt')
    else:
        return "Documentation not found", 404

if __name__ == '__main__':
    # For production, use a WSGI server (e.g., gunicorn)
    app.run(debug=True)
