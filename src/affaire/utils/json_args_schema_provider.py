import json


from src.affaire.utils.args_schema_provider_interface import ArgsSchemaProviderInterface


class JSONArgsSchemaProvider(ArgsSchemaProviderInterface):
    """
    Provide arguments schema via JSON file
    """
    def __init__(self, args_provider_path: str):
        self._args_provider_path = args_provider_path

    def load_schema(self) -> dict:
        with open(self._args_provider_path, 'rt') as f:
            try:
                return json.loads(f.read())
            except json.JSONDecodeError:
                return dict()
