import os
import shutil
import stat
import datetime
import send2trash
from pathlib import Path
from typing import List, Dict, Any, Tuple


class FileManager:
    """Class to handle file system operations."""
    
    @staticmethod
    def get_directory_contents(path: str) -> List[Dict[str, Any]]:
        """Get contents of a directory with file/folder details."""
        items = []
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                stats = os.stat(item_path)
                
                size = FileManager._get_human_readable_size(stats.st_size)
                modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                is_directory = os.path.isdir(item_path)
                extension = os.path.splitext(item)[1].lower() if not is_directory else ""
                
                items.append({
                    'name': item,
                    'path': item_path,
                    'size': size,
                    'size_bytes': stats.st_size,
                    'modified': modified,
                    'is_directory': is_directory,
                    'extension': extension
                })
                
            items.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
            
        except PermissionError:
            pass
        except Exception as e:
            print(f"Error accessing {path}: {e}")
            
        return items
    
    @staticmethod
    def create_directory(path: str) -> bool:
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            return False
    
    @staticmethod
    def rename_item(old_path: str, new_path: str) -> bool:
        try:
            os.rename(old_path, new_path)
            return True
        except Exception as e:
            print(f"Error renaming {old_path} to {new_path}: {e}")
            return False
    
    @staticmethod
    def delete_item(path: str, use_trash: bool = True) -> bool:
        try:
            if use_trash:
                send2trash.send2trash(path)
            else:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            return True
        except Exception as e:
            print(f"Error deleting {path}: {e}")
            return False
    
    @staticmethod
    def copy_item(source: str, destination: str) -> bool:
        try:
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            return True
        except Exception as e:
            print(f"Error copying {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def move_item(source: str, destination: str) -> bool:
        try:
            shutil.move(source, destination)
            return True
        except Exception as e:
            print(f"Error moving {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def get_item_properties(path: str) -> Dict[str, Any]:
        try:
            stats = os.stat(path)
            properties = {
                'name': os.path.basename(path),
                'path': path,
                'size': FileManager._get_human_readable_size(stats.st_size),
                'size_bytes': stats.st_size,
                'created': datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'accessed': datetime.datetime.fromtimestamp(stats.st_atime).strftime('%Y-%m-%d %H:%M:%S'),
                'is_directory': os.path.isdir(path),
                'is_file': os.path.isfile(path),
                'is_hidden': FileManager._is_hidden(path),
                'permissions': FileManager._get_permissions(stats.st_mode),
            }
            
            if properties['is_directory']:
                try:
                    properties['contents_count'] = len(os.listdir(path))
                except:
                    properties['contents_count'] = 'Unknown'
            
            return properties
        except Exception as e:
            print(f"Error getting properties for {path}: {e}")
            return {}
    
    @staticmethod
    def search_files(directory: str, query: str, recursive: bool = True) -> List[str]:
        results = []
        query = query.lower()
        
        try:
            if recursive:
                for root, dirs, files in os.walk(directory):
                    for dir_name in dirs:
                        if query in dir_name.lower():
                            results.append(os.path.join(root, dir_name))
                    
                    for file_name in files:
                        if query in file_name.lower():
                            results.append(os.path.join(root, file_name))
            else:
                for item in os.listdir(directory):
                    if query in item.lower():
                        results.append(os.path.join(directory, item))
        except Exception as e:
            print(f"Error searching in {directory}: {e}")
        
        return results
    
    @staticmethod
    def create_file(path: str, content: str = "") -> bool:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error creating file {path}: {e}")
            return False
    
    @staticmethod
    def get_drives() -> List[Dict[str, Any]]:
        drives = []
        
        try:
            import win32api
            import win32file
            
            drive_letters = win32api.GetLogicalDriveStrings().split('\000')[:-1]
            
            for drive in drive_letters:
                try:
                    drive_type = win32file.GetDriveType(drive)
                    drive_types = {
                        0: "Unknown",
                        1: "No Root Directory",
                        2: "Removable",
                        3: "Fixed",
                        4: "Network",
                        5: "CD-ROM",
                        6: "RAM Disk"
                    }
                    
                    drive_name = drive.replace('\\', '')  # Remove backslash
                    drive_info = {
                        'path': drive,
                        'name': f"Drive ({drive_name})",
                        'type': drive_types.get(drive_type, "Unknown")
                    }
                    
                    try:
                        sectors_per_cluster, bytes_per_sector, free_clusters, total_clusters = win32file.GetDiskFreeSpace(drive)
                        total_size = total_clusters * sectors_per_cluster * bytes_per_sector
                        free_size = free_clusters * sectors_per_cluster * bytes_per_sector
                        
                        drive_info['total_size'] = FileManager._get_human_readable_size(total_size)
                        drive_info['free_size'] = FileManager._get_human_readable_size(free_size)
                        drive_info['used_percent'] = round((1 - (free_size / total_size)) * 100, 1)
                    except:
                        pass
                    
                    drives.append(drive_info)
                except:
                    pass
        except ImportError:
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append({
                        'path': drive,
                        'name': f"Drive ({letter})",
                        'type': "Unknown"
                    })
        
        return drives
    
    @staticmethod
    def _get_human_readable_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
    
    @staticmethod
    def _is_hidden(path: str) -> bool:
        try:
            if os.name == 'nt':
                import win32api
                import win32con
                attribute = win32api.GetFileAttributes(path)
                return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
            else:
                return os.path.basename(path).startswith('.')
        except:
            return False
    
    @staticmethod
    def _get_permissions(mode: int) -> str:
        perms = ""
        
        perms += "r" if mode & stat.S_IRUSR else "-"
        perms += "w" if mode & stat.S_IWUSR else "-"
        perms += "x" if mode & stat.S_IXUSR else "-"
        
        perms += "r" if mode & stat.S_IRGRP else "-"
        perms += "w" if mode & stat.S_IWGRP else "-"
        perms += "x" if mode & stat.S_IXGRP else "-"
        
        perms += "r" if mode & stat.S_IROTH else "-"
        perms += "w" if mode & stat.S_IWOTH else "-"
        perms += "x" if mode & stat.S_IXOTH else "-"
        
        return perms