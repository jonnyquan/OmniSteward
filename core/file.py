class FileManager:
    def __init__(self):
        self.id2path = {}
        self.path2id = {}
        self.index = 0


    def is_prepared(self, file_path: str):
        return file_path in self.path2id

        
    def add(self, file_path: str):
        file_id = int(self.index)
        if self.is_prepared(file_path):
            print(f"DEBUG - 文件已存在: {file_path}")
            return self.path2id[file_path]
        else:
            self.id2path[file_id] = file_path
            self.path2id[file_path] = file_id
            self.index += 1
            print(f"DEBUG - 添加文件: {file_path}, file_id: {file_id}")
            return file_id
    
    def get(self, file_id: str):
        try:
            file_id = int(file_id)
            return self.id2path.get(file_id, None)
        except (ValueError, TypeError):
            print(f"DEBUG - 无效的file_id: {file_id}")
            return None