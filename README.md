# PyImfit

PyImfit is a Python wrapper for [Imfit](https://github.com/perwin/imfit), a C++-based program for fitting
2D models to scientific images. It is specialized for fitting astronomical images of galaxies, but can in 
principle be used to fit any 2D Numpy array of data. 

**WARNING: This is currently a work in progress, and is not yet ready for general use!**

## A Simple Example of Use

Assuming you want to fit an astronomical image named `galaxy.fits` using a model defined
in an Imfit configuration file named `config_galaxy.dat`:

    from astropy.io import fits
    import pyimfit
    
    imageFile = "<path-to-FITS-file-directory>/galaxy.fits"
    imfitConfigFile = "<path-to-config-file-directory>/config_galaxy.dat"

    # read in image data, convert to proper double-precision, little-endian format
    image_data = pyimfit.FixImage(fits.getdata(imageFile))

    # construct model from config file
    model_desc = pyimfit.ModelDescription.load(imfitConfigFile)

    # create an Imfit object, using the previously loaded model configuration
    imfit_fitter = pyimfit.Imfit(model_desc)

    # load the image data and image characteristics (the specific values are
    # for a typical SDSS r-band image, where a sky-background value of 130.14
    # has already been subtracted), and then do a standard fit
    # (using default chi^2 statistics and Levenberg-Marquardt solver)
    imfit_fitter.fit(image_data, gain=4.725, read_noise=4.3, original_sky=130.14)
    
    # check the fit and print the resulting best-fit parameter values
    if imfit_fitter.fitConverged is True:
        print("Fit converged: chi^2 = {0}, reduced chi^2 = {1}".format(imfit_fitter.fitStatistic,
            imfit_fitter.reducedFitStatistic))
        bestfit_params = imfit_fitter.getRawParameters()
        print("Best-fit parameter values:", bestfit_params)


See the Jupyter notebook `pyfit_emcee.ipynb` in the `docs` subdirectory for
an example of using PyImfit with the Markov Chain Monte Carlo code [`emcee`](http://dfm.io/emcee/current/).

Online documentation: [https://pyimfit.readthedocs.io/en/latest/](https://pyimfit.readthedocs.io/en/latest/).


## Requirements and Installation

PyImfit is designed to work with modern versions of Python 3 (nominally 3.5 or later); no support for 
Python 2 is planned.

### Standard Installation

A precompiled binary version ("wheel") of PyImfit for macOS can be **[not yet, but soon!]** installed via PyPI:

    $ pip install pyimfit

PyImfit requires the following Python libraries/packages (which will automatically be installed
by pip if they are not already present):

* Numpy
* Scipy
* Astropy -- not strictly required except for the tests; mainly useful for reading in FITS files as
numpy arrays

### Building from Source

To build PyImfit from source, you will need the following:

   * Most of the same external (C/C++) libraries that Imfit requires: specifically 
   [FFTW3](https://www.fftw.org) [version 3], [GNU Scientific Library](https://www.gnu.org/software/gsl/) [version 2.0
   or later!], and [NLopt](https://nlopt.readthedocs.io/en/latest/)
   
   * This Github repository (use `--recurse-submodules` to ensure the Imfit repo is also downloaded)
           
           $ git clone --recurse-submodules git://github.com/perwin/pyimfit.git

   * A reasonably modern C++ compiler -- e.g., GCC 4.8.1 or later, or any C++-11-aware version of 
   Clang++/LLVM that includes support for OpenMP (note that this does *not* include the Apple-built 
   version of Clang++ that comes with Xcode for macOS, since that does not include OpenMP).

   * PyImfit uses SCons to build the base Imfit library that the Python module is built on top of;
   this *should* be installed when you execute the setup.py file, if it's not already on your
   system.


#### Steps for building PyImfit from source:

1. Install necessary external libraries (FFTW3, GSL, NLopt)

    * These can be installed from source, or via package managers (e.g., Homebrew on macOS)
    
    * Note that version 2.0 or later of GSL is required!

2. Clone the PyImfit repository

       $ git clone --recurse-submodules git://github.com/perwin/pyimfit.git

3. Build the Python package

   * **[macOS only:] First, specify a valid, OpenMP-compatible C++ compiler**
   
         $ export CC=<c++-compiler-name>; export CXX=<c++-compiler-name>
        
    (You need to point CC and CXX to the *same*, C++ compiler!
    This should not be necessary on a Linux system, assuming the default compiler is standard GCC.)
   
   * Build and install PyImfit!
   
      * For testing purposes (installs a link to current directory in your usual package-install location)

            $ python3 setup.py develop

      * For general installation (i.e., actually installs the package in your usual package-install location)

            $ python3 setup.py install


## Credits

PyImfit originated as [python-imfit](https://github.com/streeto/python-imfit), written by André Luiz de Amorim; 
the current, updated version is by Peter Erwin.


## License

PyImfit is licensed under version 3 of the GNU Public License.

