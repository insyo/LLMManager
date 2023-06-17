from typing import Any
import sqlite3

from llm import FunctionCallableLLMManager


DATABASE_NAME = "demo.db"


# データベースの種類を取得する関数
def get_database_type() -> dict[str, Any]:
    """
    {
      "description": "データベースの種類を取得します",
      "parameters": []
    }
    """
    return {"status": "success", "message": "sqlite3"}


# データベース中のテーブル一覧を取得する関数
def get_tables() -> dict[str, Any]:
    """
    {
      "description": "データベース中のテーブル一覧を取得します",
      "parameters": []
    }
    """
    return {
        "status": "success",
        "message": sqlite3.connect(DATABASE_NAME)
        .cursor()
        .execute("SELECT name FROM sqlite_master WHERE type='table'")
        .fetchall(),
    }


# テーブルのスキーマを取得する関数
def get_table_schema(table_name: str) -> dict[str, Any]:
    """
    {
      "description": "テーブルのスキーマを取得します",
      "parameters": [
        { "name": "sql", "type": "string", "description": "実行したいSQL文字列を指定します"}
      ]
    }
    """
    try:
        return {
            "status": "success",
            "message": sqlite3.connect(DATABASE_NAME)
            .cursor()
            .execute(f"PRAGMA table_info({table_name})")
            .fetchall(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 参照系のSQLを実行する関数
def execute_query(sql: str) -> dict[str, Any]:
    """
    {
      "description": "参照系のSQLを実行する関数",
      "parameters": [
        { "name": "sql", "type": "string", "description": "実行したいSQL文字列を指定します"}
      ]
    }
    """
    try:
        return {
            "status": "success",
            "message": sqlite3.connect(DATABASE_NAME).cursor().execute(sql).fetchall(),
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# 更新系のSQLを実行する関数
def excute_update_query(sql: str) -> dict[str, Any]:
    """
    {
      "description": "更新系のSQLを実行する関数",
      "parameters": [
        { "name": "sql", "type": "string", "description": "実行したいSQL文字列を指定します"}
      ]
    }
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.cursor().execute(sql)
        conn.commit()
        conn.close()

        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    while True:
        question = input("質問を入力してください: ")
        if question == "exit":
            break
        model = "gpt-3.5-turbo-0613"
        # model = "gpt-4-0613"
        llm = FunctionCallableLLMManager(model=model, temperature=0.3, max_tokens=2000)
        response = llm.get_response(
            question,
            [
                get_database_type,
                get_tables,
                get_table_schema,
                execute_query,
                excute_update_query,
            ],
        )
        print(response)


if __name__ == "__main__":
    main()
