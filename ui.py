import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeView, QPushButton, QLineEdit, QLabel,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox,
    QSplitter, QStyle, QToolBar, QComboBox, QFileSystemModel
)
from PySide6.QtCore import Qt, QDir, QSize
from PySide6.QtGui import QAction, QIcon
from file_manager import FileManager

class FileManagerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.file_manager = FileManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Windows File Manager')
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.create_toolbar()

        address_layout = QHBoxLayout()
        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.setMinimumWidth(300)
        self.path_combo.currentTextChanged.connect(self.navigate_to_path)
        
        self.drive_combo = QComboBox()
        self.update_drive_list()
        self.drive_combo.currentTextChanged.connect(self.change_drive)
        
        address_layout.addWidget(QLabel("Drive:"))
        address_layout.addWidget(self.drive_combo)
        address_layout.addWidget(QLabel("Path:"))
        address_layout.addWidget(self.path_combo)
        main_layout.addLayout(address_layout)

        splitter = QSplitter(Qt.Horizontal)

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.clicked.connect(self.on_tree_view_clicked)

        for i in range(1, self.model.columnCount()):
            self.tree_view.hideColumn(i)

        self.details_view = QTreeView()
        self.details_view.setModel(self.model)
        self.details_view.setRootIndex(self.model.index(QDir.rootPath()))
        self.details_view.setSelectionMode(QTreeView.ExtendedSelection)
        self.details_view.setSortingEnabled(True)
        self.details_view.doubleClicked.connect(self.on_item_double_clicked)

        splitter.addWidget(self.tree_view)
        splitter.addWidget(self.details_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.create_menu_bar()
        
        initial_path = QDir.rootPath()
        self.navigate_to_path(initial_path)

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        back_action = QAction("Back", self)
        back_action.setStatusTip("Go back to previous directory")
        back_action.triggered.connect(self.go_back)
        toolbar.addAction(back_action)

        forward_action = QAction("Forward", self)
        forward_action.setStatusTip("Go forward to next directory")
        forward_action.triggered.connect(self.go_forward)
        toolbar.addAction(forward_action)

        up_action = QAction("Up", self)
        up_action.setStatusTip("Go up one directory")
        up_action.triggered.connect(self.go_up)
        toolbar.addAction(up_action)

        toolbar.addSeparator()

        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh current directory")
        refresh_action.triggered.connect(self.refresh)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search files...")
        self.search_box.textChanged.connect(self.search_files)
        toolbar.addWidget(self.search_box)

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        
        new_menu = QMenu("New", self)
        new_file_action = QAction("File", self)
        new_file_action.triggered.connect(self.create_new_file)
        new_folder_action = QAction("Folder", self)
        new_folder_action.triggered.connect(self.create_new_folder)
        new_menu.addAction(new_file_action)
        new_menu.addAction(new_folder_action)
        file_menu.addMenu(new_menu)

        file_menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_selected)
        file_menu.addAction(delete_action)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self.rename_selected)
        file_menu.addAction(rename_action)

        file_menu.addSeparator()

        properties_action = QAction("Properties", self)
        properties_action.triggered.connect(self.show_properties)
        file_menu.addAction(properties_action)

        edit_menu = menubar.addMenu("Edit")
        
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_selected)
        edit_menu.addAction(copy_action)

        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(self.cut_selected)
        edit_menu.addAction(cut_action)

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.paste_items)
        edit_menu.addAction(paste_action)

        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh)
        view_menu.addAction(refresh_action)

    def update_drive_list(self):
        drives = self.file_manager.get_drives()
        self.drive_combo.clear()
        for drive in drives:
            self.drive_combo.addItem(f"{drive['path']} ({drive['type']})", drive['path'])

    def change_drive(self, drive_text):
        if drive_text:
            drive_path = drive_text.split(" ")[0]
            self.navigate_to_path(drive_path)

    def navigate_to_path(self, path):
        if path and os.path.exists(path):
            self.details_view.setRootIndex(self.model.index(path))
            self.path_combo.setCurrentText(path)
            self.update_status_bar()

    def update_status_bar(self):
        current_path = self.path_combo.currentText()
        try:
            properties = self.file_manager.get_item_properties(current_path)
            if properties['is_directory']:
                status_text = f"Items: {properties.get('contents_count', 0)} | Free space: {properties.get('free_size', 'Unknown')}"
                self.status_bar.showMessage(status_text)
        except Exception as e:
            self.status_bar.showMessage(str(e))

    def on_tree_view_clicked(self, index):
        path = self.model.filePath(index)
        self.navigate_to_path(path)

    def on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.navigate_to_path(path)

    def go_back(self):
        # Implement history navigation
        pass

    def go_forward(self):
        # Implement history navigation
        pass

    def go_up(self):
        current_path = self.path_combo.currentText()
        parent_path = os.path.dirname(current_path)
        if parent_path:
            self.navigate_to_path(parent_path)

    def refresh(self):
        self.model.setRootPath(self.model.rootPath())
        self.update_status_bar()
        self.update_drive_list()

    def search_files(self, query):
        if not query:
            self.refresh()
            return

        current_path = self.path_combo.currentText()
        results = self.file_manager.search_files(current_path, query, recursive=False)
        # Implement search results display

    def create_new_file(self):
        current_path = self.path_combo.currentText()
        name, ok = QFileDialog.getSaveFileName(self, "Create New File", current_path)
        if ok and name:
            self.file_manager.create_file(name)
            self.refresh()

    def create_new_folder(self):
        current_path = self.path_combo.currentText()
        name, ok = QFileDialog.getSaveFileName(self, "Create New Folder", current_path)
        if ok and name:
            self.file_manager.create_directory(name)
            self.refresh()

    def delete_selected(self):
        selected = self.details_view.selectedIndexes()
        if not selected:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete the selected items?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            paths = set()
            for index in selected:
                if index.column() == 0:
                    paths.add(self.model.filePath(index))

            for path in paths:
                self.file_manager.delete_item(path, use_trash=True)
            
            self.refresh()

    def rename_selected(self):
        selected = self.details_view.selectedIndexes()
        if not selected:
            return

        old_path = self.model.filePath(selected[0])
        new_name, ok = QFileDialog.getSaveFileName(
            self, "Rename Item",
            old_path,
            "All Files (*.*)"
        )

        if ok and new_name:
            self.file_manager.rename_item(old_path, new_name)
            self.refresh()

    def show_properties(self):
        selected = self.details_view.selectedIndexes()
        if not selected:
            return

        path = self.model.filePath(selected[0])
        properties = self.file_manager.get_item_properties(path)
        
        msg = QMessageBox()
        msg.setWindowTitle("Properties")
        msg.setText("\n".join([f"{k}: {v}" for k, v in properties.items()]))
        msg.exec_()

    def copy_selected(self):
        # Implement copy functionality
        pass

    def cut_selected(self):
        # Implement cut functionality
        pass

    def paste_items(self):
        # Implement paste functionality
        pass

def main():
    app = QApplication(sys.argv)
    window = FileManagerUI()
    window.show()
    sys.exit(app.exec_())