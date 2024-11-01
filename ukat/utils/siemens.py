import numpy as np


def write_dvs(scheme, filepath, normalization='none',
              coordinate_system='xyz', comment='N/A'):
    """Create Siemens .dvs file for diffusion imaging acquisitions

    Parameters
    ----------
    scheme : string
        Scheme can be two types of strings:
        1) File path to a text file containing a gradient scheme (see below)
        2) A gradient scheme string (see below)

        The following is an example of a dummy gradient scheme initialised in
        the `SCHEME` varible:
            >> print(SCHEME)
             0.70710678          0.0   0.70710678      0
             0.70710678          0.0   0.70710678      5
             0.70710678          0.0   0.70710678    100
             0.70710678          0.0   0.70710678    500
            -0.70710678   0.70710678          0.0      5
            -0.70710678   0.70710678          0.0    100
            -0.70710678   0.70710678          0.0    500

        Where each row corresponds to one measurement, the first 3 columns are
        the b-vector components (b-vector with norm 1) and the 4th column is
        the b-value in s/mm2. This example shows an acquisition with 3 nonzero
        b-values (5, 100, 500), each with two directions, and one b=0 in the
        start of the acquisition. Such a gradient scheme string can be
        generated using ukat.dwi.make_gradient_scheme().
    filepath: string
        The filepath (without extension) for the .dvs file which will be
        generated by this function

    Returns
    -------
    string
        filepath of generated file, including extension
    string
        content of generated file

    Notes
    -----
    The specification for Siemens .dvs files implemented here is described in
    the Siemens syngo MR E11 Operator Manual page 140. It may not work for
    other software lines (e.g. VX*).
    Note that the validity in the formatting of the `scheme` string is not
    checked so ensure you have generated it properly as shown above.

    """

    expected_normalization = ["maximum", "unity", "none"]
    if normalization not in expected_normalization:
        raise ValueError((f"`normalization` must be one of "
                          f"{expected_normalization}"))

    expected_coordinate_system = ["xyz", "prs"]
    if coordinate_system not in expected_coordinate_system:
        raise ValueError((f"`coordinate_system` must be one of "
                          f"{expected_coordinate_system}"))

    # Quick check just to keep comments short
    good_comment = isinstance(comment, str) and len(comment) < 50
    if not good_comment:
        raise ValueError("`comment` must be a string with < 50 characters")

    if ".txt" in scheme:
        # Assume is filepath
        gt = np.loadtxt(scheme)
    else:
        # Assume is string such as those generated by make_gradient_scheme()
        gt = np.vstack([np.fromstring(x, dtype=float, sep=' ')
                        for x in scheme.split('\n')])

    bvals = gt[:, 3].astype(int)
    bvecs = gt[:, :3]
    n_bvecs = bvecs.shape[0]
    unique_bvals = np.unique(bvals)
    max_bval = np.max(unique_bvals)

    # Write custom header for reference (ignored by the scanner)
    dvs = ""
    head = ("# -----------------------------------------------------\n"
            "# .dvs file for the following setup:\n"
            "# b-val (s/mm2)  # directions\n")
    dvs = f"{dvs}{head}"

    for unique_bval in unique_bvals:
        cndirs = str(np.count_nonzero(bvals == unique_bval))
        dvs = f"{dvs}# {str(unique_bval).ljust(15)}{cndirs}\n"

    dvs = f"{dvs}# -----------------------------------------------------\n"

    # .dvs directives
    dvs = f"{dvs}\n[directions={n_bvecs}]\n"
    dvs = f"{dvs}Normalization = {normalization}\n"
    dvs = f"{dvs}CoordinateSystem = {coordinate_system}\n"
    dvs = f"{dvs}Comment = {comment}\n\n"

    # Write .dvs gradient table with scaled vectors
    for i, (bval, bvec) in enumerate(zip(bvals, bvecs)):
        x, y, z = bvec*np.sqrt(bval/max_bval)
        dvs = f"{dvs}Vector[{i}] = ( {x:.6f}, {y:.6f}, {z:.6f} )\n"

    # Write b-value table for reference (ignored by the scanner)
    for i, bval in enumerate(bvals):
        dvs = f"{dvs}\n# b-value[{i}] = {bval}"

    filepath = f"{filepath}.dvs"
    fid = open(filepath, "w")
    fid.write(dvs)
    fid.close()

    return filepath, dvs
