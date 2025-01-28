import configparser
import ipaddress
from pathlib import Path
from typing import Any, Dict, Optional

import utils.logs as logs



SectionName = str
OptionName = str
OptionValue = str
AddedOrUpdated = str


def retype_value(
    value: OptionValue, option_type: Optional[str] = None
) -> Any:
    match option_type:
        case "bool":
            value = value.lower() in ["true", "1", "t", "y", "yes", "yeah"]
        case "int":
            value = int(value)
        case "float":
            value = float(value)
        case "file":
            value = Path(value)
        case "ip":
            value = ipaddress.ip_address(value)
        case "port":
            value = int(value)
            if not 1 <= value <= 65535:
                raise ValueError
        case _:
            return value
    return value


class Configuration:
    def __init__(self) -> None:
        self._config_file: Optional[Path] = None
        self._config: Optional[configparser.ConfigParser] = None

    def load_config(self, config_file: Path) -> None:
        self._config_file: Path = config_file
        self.__parse_config()

    def __parse_config(self) -> None:
        self._config = configparser.ConfigParser()
        if not self._config_file.is_file():
            logs.critical(f"The config file '{self._config_file}' doesn't exist.")
        try:
            self._config.read(self._config_file)
        except configparser.ParsingError:
            logs.critical(
                f"The config file '{self._config_file}' contains parsing errors."
            )

    def __save_config(self) -> None:
        with open(self._config_file, "w") as fp:
            self._config.write(fp)

    @staticmethod
    def __exception_handler(message: str, value_required: bool) -> None:
        if value_required:
            logs.error(message)
        else:
            logs.warning(message)

    def exists(
        self, section: SectionName, option: OptionName
    ) -> bool:
        return self._config.has_section(section) and self._config.has_option(
            section, option
        )

    def get(
        self,
        section: SectionName,
        option: OptionName,
        required: bool = False,
    ) -> Optional[Any]:
        value = None
        option_type = "unknown"
        try:
            value = self._config.get(section, option)
        except configparser.NoSectionError:
            message = f"Unable to find section '{section}' to read the '{option}' option from the configuration file."
            self.__exception_handler(message, required)
        except configparser.NoOptionError:
            message = f"Unable to find option '{option}' in the '{section}' section of the configuration file."
            self.__exception_handler(message, required)
        try:
            option_type = option.rsplit("_", 1)[-1]
            value = retype_value(value, option_type)
        except ValueError:
            logs.error(
                f"The configuration contains invalid value for the option {section}/{option}. Expected type {option_type}."
            )
        return value

    def __getattr__(self, attribute: str) -> Optional[str]:
        parts = attribute.split("_", 1)
        if len(parts) == 1:
            return None
        section, option = parts[0], parts[1]
        value = self.get(section, option, required=True)
        return value

    def get_all_options_for_section(self, section: SectionName) -> Dict[
        SectionName,
        Dict[OptionName, OptionValue],
    ]:
        values = {section: {}}
        for option_name, option_value in self._config.items(section):
            values[section][option_name] = option_value
        return values

    def get_all_options_all_sections(
        self,
    ) -> Dict[
        SectionName,
        Dict[OptionName, OptionValue],
    ]:
        values = {}
        for section in self._config.sections():
            values[section] = {}
            for option_name, option_value in self._config.items(section):
                values[section][option_name] = option_value
        return values

    def set(
        self,
        section: SectionName,
        option: OptionName,
        value: OptionValue,
        required: bool = True,
    ) -> None:
        if type(value) is not str:
            logs.warning(
                f"The variable type {type(value)} is not a string. Variable will be converted."
            )
            value = str(value)
        if not self._config.has_section(section):
            message = f"Unable to find section '{section}' to write the option '{option}'='{value}' in the configuration file."
            self.__exception_handler(message, required)
        if not self._config.has_option(section, option):
            message = f"Unable to find option '{option}' in the '{section}' section to write the value '{value}' in the configuration file."
            self.__exception_handler(message, required)
        self._config.set(section, option, value)
        self.__save_config()

    def set_options_values(
        self,
        options: Dict[
            SectionName,
            Dict[OptionName, OptionValue],
        ],
    ) -> Dict[
        SectionName,
        Dict[OptionName, AddedOrUpdated],
    ]:
        result = {}
        for section in options:
            result[section] = {}
            if not self._config.has_section(section):
                self._config.add_section(section)
            for option_name, option_value in options[section].items():
                if self._config.has_option(section, option_name):
                    result[section][option_name] = "updated"
                else:
                    result[section][option_name] = "added"
                self._config.set(section, option_name, option_value)
        self.__save_config()
        return result


config = Configuration()
