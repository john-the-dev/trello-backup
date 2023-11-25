import trellobackup
import configme as config

def main():
    # trello = trellobackup.TrelloBackup(config.apiKey, config.appToken)
    # trello.enableBackupAttachments(config.backupAttachments)
    # trello.run()

    trello = trellobackup.TrelloBackup(config.apiKey, config.appToken)
    trello.json2txt("/users/ruiwang/Downloads/trello_work_board_20231124.json")

if __name__ == '__main__':
    # Execute only if run as a script.
    main()