import requests
import os
import config
import json
import hashlib
class Downloader:
    def __init__(self, username, token, verbose=False):
        self.username = username
        self.token = token
        self.failed_downloads = []
        self.verbose = verbose

        # If there is no 'downloads/' folder, make one
        # also if there is no 'mod-list/' folder, make one
        if not os.path.exists('downloads/'):
            os.mkdir('downloads/')
        if not os.path.exists('mod-list/'):
            os.mkdir('mod-list/')


        # Download updated mod-list.json
        self.mod_list = self.get_modlist()
        
    def get_modlist(self):
        # if the mod list already exists, download a *new* one and compare the sum,
        # we replace it if it's different
        if os.path.exists('mod-list/mod-list.json'):
            res = requests.get('https://mods.factorio.com/api/mods?page_size=max')
            open('mod-list/mod-list-new.json', 'wb').write(res.content)

            # calculate both sums
            mod_list_sha1 = self.calculate_sha1sum('mod-list/mod-list.json')
            new_mod_list_sha1 = self.calculate_sha1sum('mod-list/mod-list-new.json')
            if mod_list_sha1 == new_mod_list_sha1: # if they match, then delete updated list and load local
                if self.verbose:
                    print('Unchanched Old: {} == New: {}'.format(mod_list_sha1, new_mod_list_sha1))
                os.remove('mod-list/mod-list-new.json')
                return json.load(open('mod-list/mod-list.json'))['results']
            else: # they dont match, remove local and save new
                if self.verbose:
                    print('Old: {} -> New: {}'.format(mod_list_sha1, new_mod_list_sha1))
                os.remove('mod-list/mod-list.json')
                if self.verbose:
                    print('[-] Old mod-list.json removed...')
                if os.rename('mod-list/mod-list-new.json', 'mod-list/mod-list.json'):
                    if self.verbose:
                        print('[+] Mod list updated')
                return json.load(open('mod-list/mod-list.json'))['results']
        else: # if there is no mod-list.json, just download it
            print('[!] No mod-list.json found, retrieving....')
            res = requests.get('https://mods.factorio.com/api/mods?page_size=max')
            open('mod-list/mod-list.json', 'wb').write(res.content)
            mod_list_sha1 = self.calculate_sha1sum('mod-list/mod-list.json')
            if self.verbose:
                print('Downloaded mod-list.json\'s SHA1 -> {}'.format(mod_list_sha1))  
            return json.load(open('mod-list/mod-list.json'))['results']


    """
    {
        "name": "Age2Taunts",
        "title": "Age2Taunts",
        "owner": "Borderline-Creepy",
        "summary": "Use 11 for when your friends get run over by a train",
        "downloads_count": 10,
        "category": "non-game-changing",
        "score": 2.0,
        "latest_release": {
            "download_url": "/download/Age2Taunts/616a1913e0fed82bb6adff98",
            "file_name": "Age2Taunts_0.1.1.zip",
            "info_json": {
                "factorio_version": "1.1"
            },
            "released_at": "2021-10-16T00:13:07.744000Z",
            "version": "0.1.1",
            "sha1": "7b8b6b36c7bd7f0b6f6fbf782042d0818e64ffe2"
        }
    }
    """
    def download_mod(self, mod):
        try:
            mod_name = mod['name']
            mod_latest_release = mod['latest_release']
            mod_download_url = mod_latest_release['download_url']
            mod_file_name = mod_latest_release['file_name']
            mod_sha1 = mod_latest_release['sha1']
            mod_path = os.path.join('downloads/', mod_file_name)

            if os.path.exists(mod_path):
                local_file_sha1 = self.calculate_sha1sum(mod_path)
                if local_file_sha1 == mod_sha1:
                    if self.verbose:
                        print('[*] Mod \'{}\' already downloaded, keeping local file: {}'.format(mod_name, mod_path))
                    return True
            else:
                if self.verbose:
                    print('[-] {} not found, retrieving...'.format(mod_file_name))
                download_url = 'https://mods.factorio.com{}?username={}&token={}'.format(mod_download_url, self.username, self.token)
                res = requests.get(download_url, stream=True)
                open(mod_path, 'wb').write(res.content)
                download_sha1 = self.calculate_sha1sum(mod_path)
                if download_sha1 == mod_sha1:
                    if self.verbose:
                        print('[+] Mod SHA1 matches, keeping')
                    return True
                else:
                    if self.verbose:
                        print('[-] Mod SHA1 doesn\'t match list')
                    os.remove(mod_path)
                    return False
                

        except Exception as e:
            print(e)

    def calculate_sha1sum(self, file_path):
        BUF_SIZE = 65536  # lets read stuff in 64kb chunks
        sha1 = hashlib.sha1()
        if (os.path.exists(file_path)):
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    sha1.update(data)
            
            calculated_sha1 = sha1.hexdigest()
            return calculated_sha1

if __name__ == "__main__":
    downloader = Downloader('', '', verbose=True)
    downloader.download_mod(downloader.mod_list[0])