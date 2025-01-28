from utils import arguments


def main():
    args = arguments.parse_args()
    match args.task:
        case "init_database":
            import database.init as database_init

            database_init.create_tables()
            database_init.insert_values()
        case "calendar":
            from main_modules import calendar

            calendar.main(args.persistent_folder)
        case "cleaner":
            from main_modules import cleaner

            cleaner.main(args.persistent_folder)
        case "responder":
            from main_modules import responder

            responder.main(args.persistent_folder)
        case "server":
            from main_modules import api_server

            api_server.main(args.persistent_folder)
        case "stats":
            from main_modules import stats

            stats.main(args.persistent_folder)
        case "tests_manager":
            from main_modules import tests_manager

            tests_manager.main(args.persistent_folder)
        case _:
            raise RuntimeError("Unknown task name.")


if __name__ == "__main__":
    main()
