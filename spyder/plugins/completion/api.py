# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
Here, 'completion' are Qt objects that provide code completion, introspection
and workspace management functions.
"""


class SpyderCompletionMixin:
    """
    Spyder plugin mixin for completion clients widgets.

    All completion clients must implement this interface in order to interact
    with Spyder CodeEditor and Projects manager.
    """
    # Use this signal to send a response back to the completion manager
    # str: Completion client name
    # int: Request sequence identifier
    # dict: Response dictionary
    sig_response_ready = None  # Signal(str, int, dict)

    # Use this signal to indicate that the plugin is ready
    sig_plugin_ready = None  # Signal(str)

    def _check_interface(self):
        if getattr(self, 'sig_response_ready', None) is None:
            raise Exception(
                '`sig_response_ready = Signal(str, int, dict)` not defined!')

        if getattr(self, 'sig_plugin_ready', None) is None:
            raise Exception(
                '`sig_plugin_ready = Signal(str)` not defined!')

    def register_file(self, language, filename, codeeditor):
        """
        Register file to perform completions.

        If a language client is not available for a given file, then this
        method should keep a queue, such that files can be initialized once
        a server is available.

        Parameters
        ----------
        language: str
            Programming language of the given file
        filename: str
            Filename to register
        codeeditor: spyder.plugins.editor.widgets.codeeditor.CodeEditor
            Codeeditor to send the client configurations
        """
        raise NotImplementedError

    def send_request(self, language, req_type, req, req_id):
        """
        Process completion/introspection request from Spyder.

        Parameters
        ----------
        language: str
            Programming language for the incoming request
        req_type: str
            Type of request, one of
            :class:`spyder.plugins.completion.CompletionTypes`
        req: dict
            Request body
            {
                'filename': str,
                **kwargs: request-specific parameters
            }
        req_id: int
            Request identifier for response
        """
        raise NotImplementedError

    def send_notification(self, language, notification_type, notification):
        """
        Send notification to completion server based on Spyder changes.

        Parameters
        ----------
        language: str
            Programming language for the incoming request
        notification_type: str
            Type of request, one of
            :class:`spyder.plugins.completion.CompletionTypes`
        notification: dict
            Request body
            {
                'filename': str,
                **kwargs: request-specific parameters
            }
        """
        raise NotImplementedError

    def send_response(self, response, resp_id):
        """
        Send response for server request.

        Parameters
        ----------
        response: dict
            Response body for server
            {
                **kwargs: response-specific keys
            }
        resp_id: int
            Request identifier for response
        """
        raise NotImplementedError

    def broadcast_notification(self, notification_type, notification):
        """
        Send a broadcast notification across all programming languages.

        Parameters
        ----------
        req_type: str
            Type of request, one of
            :class:`spyder.plugins.completion.CompletionTypes`
        req: dict
            Request body
            {
                **kwargs: notification-specific parameters
            }
        req_id: int
            Request identifier for response, None if notification
        """
        raise NotImplementedError

    def update_configuration(self):
        """Handle completion option configuration updates."""
        raise NotImplementedError

    def project_path_update(self, project_path, update_kind):
        """
        Handle project path updates on Spyder.

        Parameters
        ----------
        project_path: str
            Path to the project folder modified
        update_kind: str
            Path update kind, one of
            :class:`spyder.plugins.completion.WorkspaceUpdateKind`
        """
        raise NotImplementedError

    def start_client(self, language):
        """
        Start completions/introspection services for a given language.

        Parameters
        ----------
        language: str
            Programming language to start analyzing

        Returns
        -------
        bool
            True if language client could be started, otherwise False.
        """
        raise NotImplementedError

    def stop_client(self, language):
        """
        Stop completions/introspection services for a given language.

        Parameters
        ----------
        language: str
            Programming language to stop analyzing
        """
        raise NotImplementedError

    def start(self):
        """Start completion plugin."""
        # self.sig_plugin_ready.emit(self.COMPLETION_CLIENT_NAME)
        raise NotImplementedError

    def shutdown(self):
        """Stop completion plugin."""
        raise NotImplementedError


class LSPRequestTypes:
    """Language Server Protocol request/response types."""
    # General requests
    INITIALIZE = 'initialize'
    INITIALIZED = 'initialized'
    SHUTDOWN = 'shutdown'
    EXIT = 'exit'
    CANCEL_REQUEST = '$/cancelRequest'
    # Window requests
    WINDOW_SHOW_MESSAGE = 'window/showMessage'
    WINDOW_SHOW_MESSAGE_REQUEST = 'window/showMessageRequest'
    WINDOW_LOG_MESSAGE = 'window/logMessage'
    TELEMETRY_EVENT = 'telemetry/event'
    # Client capabilities requests
    CLIENT_REGISTER_CAPABILITY = 'client/registerCapability'
    CLIENT_UNREGISTER_CAPABILITY = 'client/unregisterCapability'
    # Workspace requests
    WORKSPACE_FOLDERS = 'workspace/workspaceFolders'
    WORKSPACE_FOLDERS_CHANGE = 'workspace/didChangeWorkspaceFolders'
    WORKSPACE_CONFIGURATION = 'workspace/configuration'
    WORKSPACE_CONFIGURATION_CHANGE = 'workspace/didChangeConfiguration'
    WORKSPACE_WATCHED_FILES_UPDATE = 'workspace/didChangeWatchedFiles'
    WORKSPACE_SYMBOL = 'workspace/symbol'
    WORKSPACE_EXECUTE_COMMAND = 'workspace/executeCommand'
    WORKSPACE_APPLY_EDIT = 'workspace/applyEdit'
    # Document requests
    DOCUMENT_PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'
    DOCUMENT_DID_OPEN = 'textDocument/didOpen'
    DOCUMENT_DID_CHANGE = 'textDocument/didChange'
    DOCUMENT_WILL_SAVE = 'textDocument/willSave'
    DOCUMENT_WILL_SAVE_UNTIL = 'textDocument/willSaveWaitUntil'
    DOCUMENT_DID_SAVE = 'textDocument/didSave'
    DOCUMENT_DID_CLOSE = 'textDocument/didClose'
    DOCUMENT_COMPLETION = 'textDocument/completion'
    COMPLETION_RESOLVE = 'completionItem/resolve'
    DOCUMENT_HOVER = 'textDocument/hover'
    DOCUMENT_SIGNATURE = 'textDocument/signatureHelp'
    DOCUMENT_REFERENCES = ' textDocument/references'
    DOCUMENT_HIGHLIGHT = 'textDocument/documentHighlight'
    DOCUMENT_SYMBOL = 'textDocument/documentSymbol'
    DOCUMENT_FORMATTING = 'textDocument/formatting'
    DOCUMENT_FOLDING_RANGE = 'textDocument/foldingRange'
    DOCUMENT_RANGE_FORMATTING = 'textDocument/rangeFormatting'
    DOCUMENT_ON_TYPE_FORMATTING = 'textDocument/onTypeFormatting'
    DOCUMENT_DEFINITION = 'textDocument/definition'
    DOCUMENT_CODE_ACTION = 'textDocument/codeAction'
    DOCUMENT_CODE_LENS = 'textDocument/codeLens'
    CODE_LENS_RESOLVE = 'codeLens/resolve'
    DOCUMENT_LINKS = 'textDocument/documentLink'
    DOCUMENT_LINK_RESOLVE = 'documentLink/resolve'
    DOCUMENT_RENAME = 'textDocument/rename'
    # Spyder extensions to LSP
    DOCUMENT_CURSOR_EVENT = 'textDocument/cursorEvent'


class ClientStatus:
    Stopped = 'stopped'
    Running = 'running'


# -------------------- SERVER CONFIGURATION SETTINGS --------------------------
# Text document synchronization mode constants
class TextDocumentSyncKind:
    """Text document synchronization modes supported by a lsp-server"""
    NONE = 0  # Text synchronization is not supported
    FULL = 1  # Text synchronization requires all document contents
    INCREMENTAL = 2  # Partial text synchronization is supported


# -------------------- LINTING RESPONSE RELATED VALUES ------------------------
class DiagnosticSeverity:
    """LSP diagnostic severity levels."""
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


# -------------------- WORKSPACE CONFIGURATION CONSTANTS ----------------------
class FileChangeType:
    CREATED = 1
    CHANGED = 2
    DELETED = 3


# ----------------- AUTO-COMPLETION RESPONSE RELATED VALUES -------------------
class CompletionItemKind:
    """LSP completion element categories."""
    TEXT = 1
    METHOD = 2
    FUNCTION = 3
    CONSTRUCTOR = 4
    FIELD = 5
    VARIABLE = 6
    CLASS = 7
    INTERFACE = 8
    MODULE = 9
    PROPERTY = 10
    UNIT = 11
    VALUE = 12
    ENUM = 13
    KEYWORD = 14
    SNIPPET = 15
    COLOR = 16
    FILE = 17
    REFERENCE = 18


class SymbolKind:
    """LSP workspace symbol constants."""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26
