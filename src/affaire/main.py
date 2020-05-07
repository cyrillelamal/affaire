import sys
import os
from typing import List


from src.affaire.utils.db_settings_provider import DBSettingsProvider

from src.affaire.controllers import AffaireController
from src.affaire.views import CLIView


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

        settings_provider = DBSettingsProvider(db_path)
        controller = AffaireController(settings_provider)
        view = CLIView(controller, args)

        controller.register_observer(view)

        view.run()

    @staticmethod
    def get_db_path(args: List[str]) -> str:
        base_dir = os.path.dirname(os.path.realpath(args[0]))

        db_path = os.path.join(base_dir, 'affaire.db')
        if os.name == 'nt':
            db_path = db_path.replace('\\', '\\\\')
        DBSettingsProvider.DB_PATH = db_path

        return db_path


if __name__ == '__main__':
    Main.main(sys.argv)
