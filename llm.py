import json
from typing import Any
import openai

import config

openai.api_key = config.OPENAI_API_KEY


class LLMManager:
    """
    function callingを使用しないLLM向けクラス
    """

    def __init__(self, model: str, temperature: float, max_tokens: int) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_response(self, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["choices"][0]["message"]


class FunctionCallableLLMManager(LLMManager):
    """
    function callingを使用するLLM向けクラス
    """

    class FunctionInfo:
        """
        function callingで呼び出す関数のdocstringから情報を取得するクラス
        """

        def __init__(self, spec: str) -> None:
            self.spec: dict[str, Any] = json.loads(spec)

        @property
        def description(self) -> str:
            return self.spec["description"]

        @property
        def properties(self) -> dict[str, Any]:
            properties = {}
            for param in self.spec["parameters"]:
                properties[param["name"]] = {
                    "type": param["type"],
                    "description": param["description"],
                }
            return properties

    def create_funcion_def(self, function: callable) -> dict[str, Any]:
        """呼び出す関数のLLM向け情報を関数のdocstringから作成する"""
        function_info = self.FunctionInfo(function.__doc__)
        return {
            "name": function.__name__,
            "description": function_info.description,
            "parameters": {
                "type": "object",
                "properties": function_info.properties,
            },
        }

    def create_function_def_list(
        self, functions: list[callable]
    ) -> list[dict[str, Any]]:
        """呼び出す関数のLLM向け情報のリストを関数のリストから作成する"""
        return [self.create_funcion_def(function) for function in functions]

    def get_response(
        self,
        prompt: str,
        functions: list[callable],
    ) -> str:
        """
        LLMに対してpromptを送信し、LLMの返答を取得する。
        LLM応答にfunction callingが含まれている場合は、
        関数を呼び出してLLMとの対話を続ける
        """
        messages = [{"role": "user", "content": prompt}]

        while True:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    functions=self.create_function_def_list(functions),
                    function_call="auto",
                    messages=messages,
                )
            except Exception as ex:
                return str(ex)

            message = response["choices"][0]["message"]

            # LLM応答にfunction callingが含まれていない場合はリターン
            if not message.get("function_call"):
                return message["content"]

            function_name = message["function_call"]["name"]
            try:
                function_args = json.loads(message["function_call"]["arguments"])
            except Exception as ex:
                # 関数呼び出しエラーの場合は、エラーを返して対話を続ける
                messages.append(message)
                messages.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": '{"status": "error", "message": "' + str(ex) + '"}',
                    }
                )
                continue

            # 呼び出し対象の関数をリストから取得
            call_to_function = [
                func for func in functions if func.__name__ == function_name
            ][0]

            # 関数呼び出し
            print("=" * 30)
            print(f"{function_name}: {function_args}")
            print("-" * 30)

            try:
                function_response = json.dumps(call_to_function(**function_args))
                print(f"response: {function_response}")
                print("=" * 30)
            except Exception as e:
                function_response = json.dumps({"status": "error", "message": str(e)})

            # LLM応答と関数の戻りを対話リストに追加
            messages.append(message)
            messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            )
