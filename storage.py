from kivy.storage.jsonstore import JsonStore


class AccountStorage:
    def __init__(self):
        self.store = JsonStore('ownphotos.json')

        if not self.store.exists('accounts'):
            self.store.put('accounts', data=[])
        if not self.store.exists('accounts_selected'):
            self.store.put('accounts_selected', selected=None)

    def get_data(self):
        return self.store.get('accounts')["data"]

    def get_selected(self):
        print(self.store.get('accounts_selected'))
        return self.store.get('accounts_selected')["selected"]

    def set_selected(self, account_id):
        self.store.put("accounts_selected", selected=account_id)

    def add_account(self, url, username, password):
        accounts = self.get_data()
        accounts.append({"url": url,
                        "username": username,
                         "password": password})
        self.store.put("accounts", data=accounts)

        if self.get_selected() is None:
            self.set_selected(len(accounts) - 1)

    def get_account(self, account_id):
        a = self.get_data()
        if int(account_id) > len(a) - 1:
            return
        return a[int(account_id)]

    def get_selected_account(self):
        a = self.get_selected()
        if a is None:
            return
        print("urrrr")
        return self.get_account(a)


