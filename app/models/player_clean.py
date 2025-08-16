from app.models.database import get_db_connection
from config import Config

class Player:
    def __init__(self, id=None, name=None, email=None, phone=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
    
    @staticmethod
    def get_all():
        """Get all active players."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM players
                ORDER BY name
            ''')
            players = cursor.fetchall()
            cursor.close()
        else:
            players = conn.execute('''
                SELECT * FROM players
                ORDER BY name
            ''').fetchall()
        
        conn.close()
        return players
    
    @staticmethod
    def get_by_id(player_id):
        """Get a player by ID."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM players WHERE id = %s
            ''', (player_id,))
            player = cursor.fetchone()
            cursor.close()
        else:
            player = conn.execute('''
                SELECT * FROM players WHERE id = ?
            ''', (player_id,)).fetchone()
        
        conn.close()
        return player

    @staticmethod
    def create(name, email=None, phone=None):
        """Create a new player."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO players (name, email, phone) 
                VALUES (%s, %s, %s) RETURNING id
            ''', (name, email, phone))
            player_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
        else:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO players (name, email, phone) 
                VALUES (?, ?, ?)
            ''', (name, email, phone))
            player_id = cursor.lastrowid
            conn.commit()
        
        conn.close()
        return player_id
    
    @staticmethod
    def update(player_id, name=None, email=None, phone=None):
        """Update a player."""
        conn = get_db_connection()
        
        # Build dynamic update query
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = %s' if Config.DB_TYPE == 'postgresql' else 'name = ?')
            params.append(name)
        if email is not None:
            updates.append('email = %s' if Config.DB_TYPE == 'postgresql' else 'email = ?')
            params.append(email)
        if phone is not None:
            updates.append('phone = %s' if Config.DB_TYPE == 'postgresql' else 'phone = ?')
            params.append(phone)
        
        if not updates:
            conn.close()
            return
        
        params.append(player_id)
        param_placeholder = '%s' if Config.DB_TYPE == 'postgresql' else '?'
        
        query = f'''UPDATE players SET {", ".join(updates)} WHERE id = {param_placeholder}'''
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            cursor.close()
        else:
            conn.execute(query, params)
            conn.commit()
        
        conn.close()
    
    @staticmethod
    def delete(player_id):
        """Delete a player."""
        conn = get_db_connection()
        
        if Config.DB_TYPE == 'postgresql':
            cursor = conn.cursor()
            cursor.execute('DELETE FROM players WHERE id = %s', (player_id,))
            conn.commit()
            cursor.close()
        else:
            conn.execute('DELETE FROM players WHERE id = ?', (player_id,))
            conn.commit()
        
        conn.close()
