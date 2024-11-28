from abc import ABC, abstractmethod

class BaseConnection(ABC):

    @abstractmethod
    def configure(self, **kwargs):
        """
        Configure the connection. This should store necessary credentials
        and mark the connection as configured.
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the connection is ready for use.
        """
        pass

    @abstractmethod
    def perform_action(self, action_name, **kwargs):
        """
        Perform an action supported by this connection.
        Args:
            action_name (str): The action to perform.
            **kwargs: Data required for the action.
        Returns:
            Any: The result of the action.
        """
        pass
