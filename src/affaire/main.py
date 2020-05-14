import sys
import os
from typing import List


from src.affaire.utils import JSONSettingsProvider
from src.affaire.utils import JSONArgsSchemaProvider

from src.affaire.controllers import AffaireController
from src.affaire.views import CLIView

from src.core_modules import AbstractModel


class Main:
    """
    Configure the settings provider.
    Set the entry controller.
    Set the entry view.
    Run the view.
    """
    @staticmethod
    def main(args: List[str]):
        db_path = Main.get_db_path(args)
        settings_path = Main.get_settings_path(args)
        json_args_provider_path = Main.get_json_args_provider_path(args)

        AbstractModel.DB_PATH = db_path

        settings_provider = JSONSettingsProvider(settings_path)
        args_schema_provider = JSONArgsSchemaProvider(json_args_provider_path)

        # TODO: dispatcher interface
        controller = AffaireController(settings_provider, args_schema_provider)
        view = CLIView(controller, args)

        controller.register_observer(view)

        view.run()

    @staticmethod
    def get_base_dir(args: List[str]) -> str:
        base_dir = os.path.dirname(os.path.realpath(args[0]))

        if not args[0].endswith('main.py'):
            base_dir = os.path.join(base_dir, 'src', 'affaire')

        return base_dir

    @staticmethod
    def get_db_path(args: List[str]) -> str:
        base_dir = Main.get_base_dir(args)

        db_path = os.path.join(base_dir, 'affaire.db')
        if os.name == 'nt':
            db_path = db_path.replace('\\', '\\\\')

        return db_path

    @staticmethod
    def get_settings_path(args: List[str]) -> str:
        base_dir = Main.get_base_dir(args)

        settings_path = os.path.join(base_dir, 'settings.json')

        return settings_path

    @staticmethod
    def get_json_args_provider_path(args: List[str]) -> str:
        base_dir = Main.get_base_dir(args)

        json_args_provider_path = os.path.join(base_dir, 'args_schema.json')

        return json_args_provider_path


if __name__ == '__main__':
    Main.main(sys.argv)
