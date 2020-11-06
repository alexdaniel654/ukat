import numpy as np
import concurrent.futures
from tqdm import tqdm
from scipy.optimize import curve_fit


class T2:
    """
    Attributes
    ----------
    t2_map : np.ndarray
        The estimated T2 values in ms
    t2_err : np.ndarray
        The certainty in the fit of `t2` in ms
    m0_map : np.ndarray
        The estimated M0 values
    m0_err : np.ndarray
        The certainty in the fit of `m0`
    shape : tuple
        The shape of the T2 map
    n_te : int
        The number of TE used to calculate the map
    n_vox : int
        The number of voxels in the map i.e. the product of all dimensions
        apart from TE
    """

    def __init__(self, pixel_array, echo_list, mask=None, multithread='auto'):
        """Initialise a T2 class instance.

        Parameters
        ----------
        pixel_array : np.ndarray
            An array containing the signal from each voxel at each echo
            time with the last dimension being time i.e. the array needed to
            generate a 3D T2 map would have dimensions [x, y, z, TE].
        echo_list : list()
            An array of the echo times used for the last dimension of the
            raw data. In milliseconds.
        mask : np.ndarray, optional
            A boolean mask of the voxels to fit. Should be the shape of the
            desired T2 map rather than the raw data i.e. omit the time
            dimension.
        multithread : bool or 'auto', optional
            Default 'auto'.
            If True, fitting will be distributed over all cores available on
            the node. If False, fitting will be carried out on a single thread.
            'auto' attempts to apply multithreading where appropriate based
            on the number of voxels being fit.
        """
        # Some sanity checks
        assert (pixel_array.shape[-1]
                == len(echo_list)), 'Number of echoes does not match the ' \
                                    'number of time frames on the last axis ' \
                                    'of pixel_array'
        assert multithread is True \
            or multithread is False \
            or multithread == 'auto', 'multithreaded must be True, False or ' \
                                      'auto. You entered {}'\
                                      .format(multithread)
        self.pixel_array = pixel_array
        self.shape = pixel_array.shape[:-1]
        self.n_te = pixel_array.shape[-1]
        self.n_vox = np.prod(self.shape)
        # Generate a mask if there isn't one specified
        if mask is None:
            self.mask = np.ones(self.shape, dtype=bool)
        else:
            self.mask = mask
            # Don't process any nan values
        self.mask[np.isnan(np.sum(pixel_array, axis=-1))] = False
        self.echo_list = echo_list
        # Auto multithreading conditions
        if multithread == 'auto':
            if self.n_vox > 20:
                multithread = True
            else:
                multithread = False
        self.multithread = multithread

        # Fit data
        self.t2_map, self.t2_err, self.m0_map, self.m0_err = self.__fit__()

    def __fit__(self):

        # Initialise maps
        t2_map = np.zeros(self.n_vox)
        t2_err = np.zeros(self.n_vox)
        m0_map = np.zeros(self.n_vox)
        m0_err = np.zeros(self.n_vox)
        mask = self.mask.flatten()
        signal = self.pixel_array.reshape(-1, self.n_te)
        # Get indices of voxels to process
        idx = np.argwhere(mask).squeeze()

        # Multithreaded method
        if self.multithread:
            with concurrent.futures.ProcessPoolExecutor() as pool:
                with tqdm(total=idx.size) as progress:
                    futures = []

                    for ind in idx:
                        future = pool.submit(self.__fit_signal__,
                                             signal[ind, :],
                                             self.echo_list)
                        future.add_done_callback(lambda p: progress.update())
                        futures.append(future)

                    results = []
                    for future in futures:
                        result = future.result()
                        results.append(result)
            t2_map[idx], t2_err[idx], m0_map[idx], m0_err[idx] = [np.array(
                row) for row in zip(*results)]

        # Single threaded method
        else:
            with tqdm(total=idx.size) as progress:
                for ind in idx:
                    sig = signal[ind, :]
                    t2_map[ind], t2_err[ind], m0_map[ind], m0_err[ind] = \
                        self.__fit_signal__(sig, self.echo_list)
                    progress.update(1)

        # Reshape results to raw data shape
        t2_map = t2_map.reshape(self.shape)
        t2_err = t2_err.reshape(self.shape)
        m0_map = m0_map.reshape(self.shape)
        m0_err = m0_err.reshape(self.shape)

        return t2_map, t2_err, m0_map, m0_err

    @staticmethod
    def __fit_signal__(sig, te):

        # Initialise parameters
        bounds = ([0, 0], [700, 1000000])
        initial_guess = [20, 10000]

        # Fit data to equation
        try:
            popt, pcov = curve_fit(two_param_eq, te, sig,
                                   p0=initial_guess, bounds=bounds)
        except RuntimeError:
            popt = np.zeros(2)
            pcov = np.zeros((2, 2))

        # Extract fits and errors from result variables
        if popt[0] < bounds[1][0] - 1:
            t2 = popt[0]
            m0 = popt[1]
            err = np.sqrt(np.diag(pcov))
            t2_err = err[0]
            m0_err = err[1]
        else:
            t2, m0, t2_err, m0_err = 0, 0, 0, 0

        return t2, t2_err, m0, m0_err

    def r2_map(self):
        """
        Generates the R2 map from the T2 map output by initialising this
        class.

        Parameters
        ----------
        See class attributes in __init__

        Returns
        -------
        r2 : np.ndarray
            An array containing the R2 map generated
            by the function with R2 measured in ms.
        """
        return np.reciprocal(self.t2_map)


def two_param_eq(t, t2, m0):
    """
        Calculate the expected signal from the equation
        signal = M0 * exp(-t / T2)

        Parameters
        ----------
        t: list
            The times the signal will be calculated at
        t2: float
            The T2 of the signal
        m0: float
            The M0 of the signal

        Returns
        -------
        signal: np.ndarray
            The expected signal
        """
    return np.sqrt(np.square(m0 * np.exp(-t / t2)))