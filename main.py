import trellobackup
import config as config

def main():
    trello = trellobackup.TrelloBackup(config.apiKey, config.appToken)
    trello.enableBackupAttachments(config.backupAttachments)
    trello.run()

if __name__ == '__main__':
    # Execute only if run as a script.
    main()