import requests
import datetime
import os
import json
from sanitize_filename import sanitize

class ConfigError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else ''

class SaveError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else ''

class APIError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else ''

class TrelloBackup:
    backupAttachments = False
    def __init__(self, apiKey, appToken):
        self.apiKey = apiKey
        self.appToken = appToken

    def save(self, fileName, fileContent):
        filePath = '{}/{}'.format(self.backupFolder, fileName)
        print('Saving content to file {}, {} bytes'.format(filePath, len(fileContent)))
        if not os.path.exists(self.backupFolder):
            try:
                os.makedirs(self.backupFolder)
            except:
                raise SaveError('Failed to create backup folder {}.'.format(self.backupFolder))
        with open(filePath, 'w') as f:
            f.write(fileContent)

    # If enable is True, download and save attachments.
    def enableBackupAttachments(self, enable):
        self.backupAttachments = enable

    def run(self):
        if len(self.apiKey) < 32: raise ConfigError('API key not set.')
        if len(self.appToken) < 32: 
            # https://trello.com/app-key
            # Request a read-only application token which never expires.
            url = 'https://trello.com/1/authorize?key={}&name=My+Backup+App&expiration=never&response_type=token&scope=read'.format(self.apiKey)
            print('Application token not set. Please visit {} in your browser to create an application token.'.format(url))
            return

        # Use backup time as folder name.
        self.backupFolder = 'backups/{}'.format(sanitize(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        # Fetch all boards.
        response = requests.get("https://api.trello.com/1/members/me/boards?key={}&token={}".format(self.apiKey, self.appToken))
        boards = json.loads(response.text)
        if not boards: raise APIError('Error fetching boards. ' + response.text)
        
        # Fetch boards in organizations.
        response = requests.get("https://api.trello.com/1/members/me/organizations?key={}&token={}".format(self.apiKey, self.appToken))
        orgs = json.loads(response.text)
        orgsDict = {}
        for org in orgs:
            response = requests.get("https://api.trello.com/1/organizations/{}/boards?&key={}&token={}".format(org['id'], self.apiKey, self.appToken))
            orgBoards = json.loads(response.text)
            if not orgBoards: raise APIError('Error fetching organization boards. ' + response.text)
            boards.extend(orgBoards)
            orgsDict[org['id']] = org
        
        # Load content for each board and save it to file.
        for board in boards:
            orgName = orgsDict[board['idOrganization']]['displayName'] if board['idOrganization'] != None else ''
            print('Fetching board {} in organization {}'.format(board['name'], orgName))
            fetchURL = 'https://api.trello.com/1/boards/{}?actions=all&actions_limit=1000&card_attachment_fields=all&cards=all&lists=all&members=all&member_fields=all&card_attachment_fields=all&checklists=all&fields=all&key={}&token={}'.format(board['id'], self.apiKey, self.appToken)
            response = requests.get(fetchURL)
            jsonObj = json.loads(response.text)
            if not jsonObj: raise APIError('Error fetching the content of board "{}". '.format(board['name']) + response.text)
            fileName = sanitize('org-{}-board-{}.json'.format(orgName, board['name']))
            self.save(fileName, response.text)

            if self.backupAttachments:
                for action in jsonObj['actions']:
                    # There is attachment data and the attachment has url.
                    if 'attachment' in action['data'] and 'url' in action['data']['attachment']:
                        attachment = action['data']['attachment']
                        print('>>>>Fetching attachment {}: {}'.format(attachment['id'], attachment['name']))
                        response = requests.get(attachment['url'])
                        fileName = sanitize('attachment-{}-{}'.format(attachment['id'], attachment['name']))
                        self.save(fileName, response.text)
        
        print('Done! {} trello boards have been downloaded and saved in "{}" folder.'.format(len(boards), self.backupFolder))

