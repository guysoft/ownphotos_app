#!/usr/bin/env python3
import threading
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.app import runTouchApp, App
from ownphotos_client import OwnphotosAPI
from kivy.clock import Clock, mainthread
from kivy.core.image import Image as CoreImage
from kivy.uix.actionbar import ActionBar
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, ListProperty
from kivy.lang import Builder
from storage import AccountStorage
from kivy.factory import Factory

try:
    from android.permissions import Permission, request_permission, check_permission
except ImportError:
    android = None
import time
import requests
import io
import os

# Create the manager
sm = ScreenManager()


def callback(scr_name, instance):
    print('The button <%s> is being pressed' % instance.text)
    sm.current = 'Title ' + str(scr_name)


def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)


class ScreenOne(Screen):
    pass


class ScreenAccounts(Screen):
    def update_accounts(self):
        print("updating accounts")
        account_storage = AccountStorage()
        accounts = account_storage.get_data()
        self.ids["accounts"].items = accounts
        self.ids["accounts_scroll"].size_hint = (1, None)

    def select_account(self, account_id):
        account_storage = AccountStorage()
        account_storage.set_selected(account_id)
        self.update_accounts()
        # popup = Popup(title='please restart', content=Label(text='Please for new account to take effect'),
        #               auto_dismiss=False)
        # popup.open()
        # Factory.Message().changeText('Please for new account to take effect')
        Factory.Message().open()

        return


class GalleryNavigation(ActionBar):
    pass


class AccountsNavigation(ActionBar):
    def add_account(self):
        obj = LoginDialog(self)
        # obj.call_pops(1)
        obj.open()


class Accounts(BoxLayout):
    # items = ListProperty([{'title': 'Another item3333'}, {'title': 'Another item33'}])\
    items = ListProperty()
    item_template = StringProperty('DataViewItem')

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        # self.bind(minimum_height=self.setter('height'))

        account_storage = AccountStorage()
        accounts = account_storage.get_data()
        self.items = accounts

    def on_items(self, *args):
        self.clear_widgets()
        print("Building account page")

        selected = AccountStorage().get_selected()

        for account_id, item in enumerate(self.items):
            print("bbb")
            print(item)
            item["account_id"] = str(account_id)
            if int(selected) == int(account_id):
                item["url"] += " (selected)"
            w = Builder.template(self.item_template, **item)

            self.add_widget(w)


class LoginDialog(Popup):
    _url = StringProperty()
    _user = StringProperty()
    _password = StringProperty()

    error = StringProperty()

    def __init__(self, parent, *args):
        super(LoginDialog, self).__init__(*args)
        # self.parent = parent
        # self.bind(_age=self.parent.setter('age'))

    def on_error(self, inst, text):
        if text:
            self.lb_error.size_hint_y = 1
            self.size = (700, 700)
        else:
            self.lb_error.size_hint_y = None
            self.lb_error.height = 0
            self.size = (700, 700)

    def _enter(self):
        if not self.url:
            self.error += "Error: Fill in url"
        elif not self.username:
            self.error += "Error: Fill in the username"
        elif not self.password:
            self.error += "Error: Fill in password"
        else:
            # print(self.url)
            # print(self.username)
            # print(self.password)

            account_storage = AccountStorage()
            account_storage.add_account(self.url, self.username, self.password)

            self.dismiss()

            app = App.get_running_app()
            app.root.get_screen(app.root.current).update_accounts()

    def _cancel(self):
        self.dismiss()


class Gallery(GridLayout):
    def do_print(self):
        threading.Thread(target=self.second_thread, args=()).start()
        # Clock.schedule_once(lambda dt: self.second_thread(), 1)

    def second_thread(self):
        print("wee")
        time.sleep(5)
        print("yay")
        self.update_label_text()
        return

    @mainthread
    def update_label_text(self):
        #
        return
    
    def get_permissions_and_run_func(self, func, clock=False):
        try:            
            write_external_storage = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
            print(write_external_storage, flush=True)
            if write_external_storage is not None and write_external_storage:
                print("we")
            else:
                request_permission(Permission.WRITE_EXTERNAL_STORAGE)
                Clock.schedule_once(lambda dt: self.get_permissions_and_run_func(func, clock), 0.5)
        except NameError:
                print("not android")

        finally:
            if clock:
                Clock.schedule_once(lambda dt: func())
            else:
                threading.Thread(target=self.build_gallery, args=()).start()
        return

    def __init__(self, **kwargs):
        GridLayout.__init__(self, **kwargs)
        self.bind(minimum_height=self.setter('height'))
        
        # Get External permissions and start Gallery
        print("Getting permissions")
        threading.Thread(target=self.get_permissions_and_run_func, args=(self.build_gallery,)).start()

        print("build gallery")
        # Clock.schedule_once(lambda dt: self.build_gallery())
        
    @mainthread
    def build_gallery_widgets(self):
        print("Adding widgets")
        # app = App.get_running_app()
        # app.ids.gallery_status.text = "Adding widgets"

        count = 0
        images_widgets = []
        for photo_date_group in self.photo_date_groups:
            if count > 10:
                break
            for photo in photo_date_group["photos"]:
                image = Image(source="", size_hint=(None, None),
                              keep_ratio=True,
                              size=(Window.width, Window.height))
                self.add_widget(image)
                self.add_widget(Button(text=str(photo["image_hash"]), size_hint_y=None, height=40))
                images_widgets.append(image)
                count += 1

        print("done adding widgets")
        threading.Thread(target=self.download_gallery_images, args=(images_widgets,)).start()
        # Clock.schedule_once(lambda dt: self.download_gallery_images(images_widgets), 1)
        return

    def download_gallery_images(self, images_widgets):
        count = 0
        try:
            for photo_date_group in self.photo_date_groups:       
                if count > 10:
                    break
                for photo in photo_date_group["photos"]:
                    
                    image_hash = photo["image_hash"]
                    print(image_hash)
                    image_path = os.path.join(self.image_cache, image_hash + ".jpg")
                    """
                    if not os.path.isfile(image_path):
                        image_data = a.get_thumbnail(photo["image_hash"])
                        
                        with open(image_path, "wb") as w:
                            w.write(image_data)
                        
                    with open(image_path, "rb") as data:
                        threading.Thread(target=self.add_image, args=(data, image_hash)).start()
                    """

                    if not os.path.isfile(image_path):
                        image_data = self.client.get_thumbnail(photo["image_hash"])                            
                        with open(image_path, "wb") as w:
                            w.write(image_data)
                    else:
                        time.sleep(1)
                    
                    print(len(images_widgets))
                    print(count)
                    print(images_widgets[count])
                    a = images_widgets[count]
                    
                    # Clock.schedule_once(lambda dt: self.add_image(image_path, a, image_hash))
                        
                    threading.Thread(target=self.add_image, args=(image_path, a, image_hash)).start()
                    count += 1

        except requests.exceptions.ConnectionError as e:
            print(e)
            print("Failed to connect")
        return
    
    def get_storage_folder(self):
        self.image_cache =  os.path.expanduser(os.path.join("~/.ownphotos/cache"))
        
        if "SECONDARY_STORAGE" in os.environ and os.path.isdir(os.path.join(os.environ["SECONDARY_STORAGE"], "Android", "data", "org.test.myapp")):
            self.image_cache = os.path.join(os.environ["SECONDARY_STORAGE"], "Android", "data", "org.test.myapp", "files", "ownphotos", "cache")
        if "EXTERNAL_STORAGE" in os.environ:
            self.image_cache = os.path.join(os.environ["EXTERNAL_STORAGE"], "Android", "data", "org.test.myapp", "files", "ownphotos", "cache")
                
        ensure_dir(self.image_cache)

    def build_gallery(self):
        self.get_storage_folder()

        account = AccountStorage().get_selected_account()
        if account is not None:
            url = account["url"]
            username = account["username"]
            password = account["password"]

            try:
                self.client = OwnphotosAPI(url, username, password, False)
                print(self.client.avilable())

                # Make sure the height is such that there is something to scroll.
                self.photo_date_groups = self.client.get_photos_by_date()["results"]
                # threading.Thread(target=self.build_gallery_widgets, args=()).start()
                Clock.schedule_once(lambda dt: self.build_gallery_widgets())
            except requests.exceptions.ConnectionError as e:
                print(e)
                print("Failed to connect")
        else:
            print("No account is set, instruct user to set one")
        return
            
    @mainthread
    def add_image(self, image_path, image, image_hash):
        print(image_hash)
        try:
            with open(image_path, "rb") as f:
                data = io.BytesIO(f.read())
            im = CoreImage(data, ext="jpg", filename=image_hash + ".png")

            image.texture = im.texture
            image.reload()
        except:
            print("failed to load image: " + image_hash + ".png")
            print("delteing bad image cache")
            os.unlink(image_path)


print("################################################")


class OwnphotosApp(App):
    pass


if __name__ == '__main__':
    OwnphotosApp().run()


# runTouchApp(sm)
