from datetime import datetime
import pprint
import re
from uuid import uuid4


from . import supabase

NAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")

class App:
    table = "paatr-app"

    def __init__(self, user_id, name, description, created_at=None, 
                    updated_at=None, deleted=False, app_id=None, repo={}, id=None, **kwargs):
        """
        Creates a new App object.

        Args:
            user_id (str): The user's ID.
            name (str): The name of the app.
            description (str): The description of the app.
            created_at (datetime): The date the app was created.
            updated_at (datetime): The date the app was last updated.
            app_id (str): The app's ID.
            repo (dict): The app's repository data.
        
        Raises:
            ValueError: If the name is invalid. 
        """

        if not self.valid_name(name):
            raise ValueError("Invalid name")

        if len(description) > 100:
            raise ValueError("Description too long")
        
        name = name.lower()

        if not app_id:
            if App.get_by("name", name):
                raise ValueError("Name already taken")
            
        self.app_id = app_id or uuid4()
        self.user_id = user_id
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.deleted = deleted
        self.repo = repo 
        self.id = id

    @classmethod
    def get_all(cls):
        """Retrieves all apps."""
        data = supabase.table(cls.table).select("*").execute()
        return data

    @classmethod
    def get(cls, app_id):
        """
        Retrieves an app by its ID.
        
        Args:
            app_id (str): The app's ID.
        
        Returns:
            App: The app object.
        """
        data = supabase.table(cls.table).select("*").eq("app_id", app_id).execute()
        if not data.data:
            return None

        return cls.from_dict(**data.data[0])
    
    @classmethod
    def get_by(cls, key, value):
        """
        Retrieves an app by a key and value.
        
        Args:
            key (str): The key to search by.
            value (str): The value to search by.
        
        Returns:
            App: The app object.
        """
        data = supabase.table(cls.table).select("*").eq(key, value).execute()
        print(data)
        if not data.data:
            return None
        
        return cls.from_dict(**data.data[0])

    def register(self):
        """Registers the app."""
        data = supabase.table(self.table).insert(self.to_dict()).execute()
        return data

    def update(self, app_id, value):
        """Updates the app's value."""
        data = supabase.table(self.table).update(value).eq("app_id", app_id).execute()
        return data
    
    def delete(self):
        data = supabase.table(self.table).update({"deleted": True}).eq("app_id", self.app_id).execute()
        return data

    def to_dict(self):
        return {
            "app_id": str(self.app_id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted": self.deleted,
            "id": self.id
        }

    @classmethod
    def from_dict(cls, **kwargs):
        """Creates an App object from a dictionary."""
        return cls(**kwargs)

    def valid_name(self, name):
        """Checks if the name is valid."""
        return NAME_REGEX.fullmatch(name)

    def __repr__(self):
        return pprint.pformat(self.to_dict())
    

