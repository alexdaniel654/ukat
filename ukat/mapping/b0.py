import os
import numpy as np
import nibabel as nib
from skimage.restoration import unwrap_phase
from ukat.utils.tools import convert_to_pi_range


class B0:
    """
    Generates a B0 map from a series of volumes collected
    with 2 different echo times.

    Attributes
    ----------
    b0_map : np.ndarray
        The estimated B0 values in Hz
    shape : tuple
        The shape of the B0 map
    mask : np.ndarray
        A boolean mask of the voxels to fit
    n_te : int
        The number of TE used to calculate the map
    delta_te : float
        The difference between the second and the first Echo Time
    phase0 : np.ndarray
        The phase image corresponding to the first Echo Time
    phase1 : np.ndarray
        The phase image corresponding to the second Echo Time
    phase_difference : np.ndarray
        The difference between the 2 phase images
    """

    def __init__(self, pixel_array, echo_list, affine=None, mask=None,
                 unwrap=True, wrap_around=False):
        """Initialise a T1 class instance.

        Parameters
        ----------
        pixel_array : np.ndarray
            A 4D/3D array containing the phase image at each
            echo time i.e. the dimensions of the array are
            [x, y, TE] or [x, y, z, TE].
        echo_list : list
            An array of the echo times in ms used for the last dimension of the
            raw data.
        affine : np.ndarray, optional
            The matrix that represents the affine transformation. It can be
            used to save images as NIFTI files. Affine transformations are
            normally used to correct for geometric distortions or deformations.
        mask : np.ndarray, optional
            A boolean mask of the voxels to fit. Should be the shape of the
            desired B0 map rather than the raw data i.e. omit the echo times
            dimension.
        unwrap : boolean, optional
            By default, this script applies the
            scipy phase unwrapping for each phase echo image.
        wrap_around : boolean, optional
            By default, this flag from unwrap_phase is False.
            The algorithm will regard the edges along the corresponding axis
            of the image to be connected and use this connectivity to guide the
            phase unwrapping process.Eg., voxels [0, :, :] are considered to be
            next to voxels [-1, :, :] if wrap_around=True.
        """

        self.pixel_array = pixel_array
        self.shape = pixel_array.shape[:-1]
        self.n_te = pixel_array.shape[-1]
        self.affine = affine
        # Generate a mask if there isn't one specified
        if mask is None:
            self.mask = np.ones(self.shape, dtype=bool)
        else:
            self.mask = mask
        if self.n_te == len(echo_list) and self.n_te == 2:
            # Get the Echo Times
            echo0 = echo_list[0]
            echo1 = echo_list[1]
            # Calculate DeltaTE in seconds
            self.delta_te = np.absolute(echo1 - echo0) * 0.001
            # Extract each phase image, mask them and rescale to
            # [-pi, pi] if not in that range already.
            self.phase0 = np.ma.masked_array(
                            convert_to_pi_range(np.squeeze(
                                self.pixel_array[..., 0])), mask=mask)
            self.phase1 = np.ma.masked_array(
                            convert_to_pi_range(np.squeeze(
                                self.pixel_array[..., 1])), mask=mask)
            if unwrap:
                # Unwrap each phase image
                self.phase0 = unwrap_phase(self.phase0,
                                           wrap_around=wrap_around)
                self.phase1 = unwrap_phase(self.phase1,
                                           wrap_around=wrap_around)
            # Phase difference
            self.phase_difference = self.phase1 - self.phase0
            # B0 Map calculation
            self.b0_map = self.phase_difference / (2 * np.pi * self.delta_te)
        else:
            raise ValueError('The input should contain 2 echo times.'
                             'The last dimension of the input pixel_array must'
                             'be 2 and the echo_list must only have 2 values.')

    def to_nifti(self, output_directory=os.getcwd(), base_file_name='Output',
                 maps='all'):
        """
        This function converts some of the B0 class attributes to NIFTI.
        """
        if not os.path.exists(output_directory):
            raise ValueError('Output directory doesn\'t exist and needs'
                             'to be created first')
        base_path = os.path.join(output_directory, base_file_name)
        if (not isinstance(self.affine, np.ndarray) and
           not isinstance(self.affine, list)):
            raise TypeError('No NIFTI file saved because no affine '
                            'matrix was provided.')
        if np.shape(self.affine) != (4, 4):
            raise ValueError('No NIFTI file saved because the provided affine '
                             'is not a 4x4 matrix.')
        if maps == 'all' or maps == ['all']:
            # Save all maps
            b0_nifti = nib.Nifti1Image(self.b0_map, affine=self.affine)
            nib.save(b0_nifti, base_path + '_b0_map.nii.gz')
            mask_nifti = nib.Nifti1Image(self.mask.astype(int),
                                         affine=self.affine)
            nib.save(mask_nifti, base_path + '_mask.nii.gz')
            phase0_nifti = nib.Nifti1Image(self.phase0, affine=self.affine)
            nib.save(phase0_nifti, base_path + '_phase0.nii.gz')
            phase1_nifti = nib.Nifti1Image(self.phase1, affine=self.affine)
            nib.save(phase1_nifti, base_path + '_phase1.nii.gz')
            phase_diff_nifti = nib.Nifti1Image(self.phase_difference,
                                               affine=self.affine)
            nib.save(phase_diff_nifti, base_path + '_phase_difference.nii.gz')
        elif isinstance(maps, list):
            for result in maps:
                if result == 'b0' or result == 'b0_map':
                    b0_nifti = nib.Nifti1Image(self.b0_map, affine=self.affine)
                    nib.save(b0_nifti, base_path + '_b0_map.nii.gz')
                elif result == 'mask':
                    mask_nifti = nib.Nifti1Image(self.mask.astype(int),
                                                 affine=self.affine)
                    nib.save(mask_nifti, base_path + '_mask.nii.gz')
                elif result == 'phase0':
                    phase0_nifti = nib.Nifti1Image(self.phase0,
                                                   affine=self.affine)
                    nib.save(phase0_nifti, base_path + '_phase0.nii.gz')
                elif result == 'phase1':
                    phase1_nifti = nib.Nifti1Image(self.phase1,
                                                   affine=self.affine)
                    nib.save(phase1_nifti, base_path + '_phase1.nii.gz')
                elif result == 'phase_difference':
                    phase_diff_nifti = nib.Nifti1Image(self.phase_difference,
                                                       affine=self.affine)
                    nib.save(phase_diff_nifti, base_path +
                             '_phase_difference.nii.gz')
        else:
            raise ValueError('No NIFTI file saved. The variable "maps" '
                             'should be "all" or a list of maps from '
                             '"["b0","mask", "phase0", "phase1", '
                             '"phase_difference"]".')

        return
