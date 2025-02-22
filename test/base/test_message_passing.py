"""Test the message passing module."""
import pytest
import torch

from topomodelx.base.message_passing import MessagePassing
from topomodelx.utils.scatter import scatter


class TestMessagePassing:
    """Test the MessagePassing class."""

    def setup_method(self, method):
        """Make message_passing object."""
        self.message_passing = MessagePassing()

    def test_reset_parameters(self):
        """Test the reset of the parameters."""
        gain = 1.0
        with pytest.raises(RuntimeError):
            self.message_passing.initialization = "invalid"
            self.message_passing.reset_parameters(gain=gain)

        # Test xavier_uniform initialization
        self.message_passing.initialization = "xavier_uniform"
        self.message_passing.weight = torch.nn.Parameter(torch.Tensor(3, 3))
        self.message_passing.reset_parameters(gain=gain)
        assert self.message_passing.weight.shape == (3, 3)

        # Test xavier_normal initialization
        self.message_passing.initialization = "xavier_normal"
        self.message_passing.weight = torch.nn.Parameter(torch.Tensor(3, 3))
        self.message_passing.reset_parameters(gain=gain)
        assert self.message_passing.weight.shape == (3, 3)

    def custom_message(self, x):
        """Make custom message function."""
        return x

    def test_propagate(self):
        """Test propagate."""
        x = torch.tensor([[1, 2], [3, 4], [5, 6]])
        neighborhood = torch.sparse_coo_tensor(
            torch.tensor([[0, 0, 0, 1, 1, 2], [0, 1, 2, 1, 2, 2]]),
            torch.tensor([1, 2, 3, 4, 5, 6]),
            size=(3, 3),
        )
        self.message_passing.message = self.custom_message.__get__(self.message_passing)
        result = self.message_passing.propagate(x, neighborhood)
        expected_shape = (3, 2)
        assert result.shape == expected_shape

    def test_sparsify_message(self):
        """Test sparsify_message."""
        x = torch.tensor(
            [
                [
                    1,
                    2,
                ],
                [3, 4],
                [5, 6],
            ]
        )
        neighborhood = torch.sparse_coo_tensor(
            torch.tensor([[0, 0, 0, 1, 1, 2], [0, 1, 2, 1, 2, 2]]),
            torch.tensor([1, 2, 3, 4, 5, 6]),
            size=(3, 3),
        )
        self.message_passing.message = self.custom_message.__get__(self.message_passing)
        _ = self.message_passing.propagate(x, neighborhood)
        x_sparse = self.message_passing.sparsify_message(x)
        expected = torch.tensor([[1, 2], [3, 4], [5, 6], [3, 4], [5, 6], [5, 6]])
        assert torch.allclose(x_sparse, expected)

    def test_get_x_i(self):
        """Test get_x_i."""
        x = torch.Tensor([[[1, 2, 3], [4, 5, 6], [7, 8, 9]]])
        self.message_passing.target_index_i = torch.LongTensor([1, 2, 0])
        result = self.message_passing.get_x_i(x)
        expected = torch.Tensor([[4, 5, 6], [7, 8, 9], [1, 2, 3]])
        assert torch.allclose(result, expected)

    def test_aggregate(self):
        """Test aggregate."""
        x = torch.tensor([[1, 2], [3, 4], [5, 6]])
        neighborhood = torch.sparse_coo_tensor(
            torch.tensor([[0, 0, 0, 1, 1, 2], [0, 1, 2, 1, 2, 2]]),
            torch.tensor([1, 2, 3, 4, 5, 6]),
            size=(3, 3),
        )
        neighborhood_values = neighborhood.coalesce().values()
        self.message_passing.message = self.custom_message.__get__(self.message_passing)
        _ = self.message_passing.propagate(x, neighborhood)
        x = self.message_passing.sparsify_message(x)
        x = neighborhood_values.view(-1, 1) * x
        result = self.message_passing.aggregate(x)
        expected = torch.tensor([[22, 28], [37, 46], [30, 36]])
        assert torch.allclose(result, expected)

    def test_forward(self):
        """Test forward."""
        x = torch.tensor([[1, 2], [3, 4], [5, 6]])
        neighborhood = torch.sparse_coo_tensor(
            torch.tensor([[0, 0, 0, 1, 1, 2], [0, 1, 2, 1, 2, 2]]),
            torch.tensor([1, 2, 3, 4, 5, 6]),
            size=(3, 3),
        )
        self.message_passing.message = self.custom_message.__get__(self.message_passing)
        result = self.message_passing.forward(x, neighborhood)
        expected_shape = (3, 2)
        assert result.shape == expected_shape
