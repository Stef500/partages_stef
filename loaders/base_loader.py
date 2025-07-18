import os, traceback
from abc import ABC, abstractmethod
from datasets import load_dataset, Dataset
from .utils import load_local, clean_example
from typing import Optional


class BaseLoader(ABC):
    """Common Loader.

    Base class for all data loaders. It provides a common interface for loading
    and processing datasets.

    Parameters
    ----------
    source : str
        Name of the data source.
    path : str
        Path to the dataset, can be a local directory or a Hugging Face Hub ID.
    subset : str, optional
        Name of the subset to load, if applicable. Defaults to None.
    source_split : str, optional
        Name of the split to load from the source. Defaults to "train".

    Attributes
    ----------
    source : str
        Name of the data source.
    path : str
        Path to the dataset.
    split : str
        Name of the split to load.
    subset : str or None
        Name of the subset to load.
    stream : bool
        Whether to stream the dataset. Defaults to False.
    """

    def __init__(self, source: str, path: str, subset: Optional[str] = None, source_split: str = "train") -> None:
        self.source = source
        self.path = path
        self.split = source_split
        self.subset = subset
        self.stream = False

    @abstractmethod
    def postprocess(self, dataset: Dataset, subset: Optional[str] = None, split: str = "train") -> Dataset:
        """Perform dataset-specific postprocessing.

        This abstract method should be implemented by subclasses to handle tasks.

        Parameters
        ----------
        dataset : Dataset
            The input dataset to postprocess.
        subset : str, optional
            Name of the subset being processed. Defaults to None.
        split : str, optional
            Name of the split being processed. Defaults to "train".

        Returns
        -------
        Dataset
            The processed dataset.
        """
        ...

    def load(self) -> Dataset:
        """Load the dataset.

        This method handles the loading of the dataset from either a local path
        or the Hugging Face Hub. It then applies postprocessing and a common
        preprocessing function.

        Returns
        -------
        Dataset
            The loaded and processed dataset.

        Raises
        ------
        RuntimeError
            If the dataset cannot be loaded.
        """
        load_fn = load_local if os.path.isdir(self.path) else load_dataset
        try:
            tmp_ds = load_fn(
                path=self.path,
                data_dir=self.subset,
                split=self.split,
                streaming=self.stream,
                trust_remote_code=True,
            )
            ds = self.postprocess(dataset=tmp_ds, subset=self.subset, split=self.split)
            ds = ds.map(clean_example, fn_kwargs={"lower": False, "rm_new_lines": False})
            # print(ds[:5]["text"]) # DEBUG
            return ds
        except Exception as e:
            raise RuntimeError(f"Impossible to load this dataset:\n {traceback.format_exc()}") from e
