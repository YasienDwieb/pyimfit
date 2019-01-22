"""
Modification of Andre's "model.py" (originally created Sep 2013).
"""

from copy import copy, deepcopy
import numpy as np



__all__ = ['SimpleModelDescription', 'ModelDescription',
           'ParameterDescription', 'FunctionDescription', 'FunctionSetDescription']



class ParameterDescription(object):
    """
    Holds information for a single parameter of an Imfit image function
    (corresponding to what is encoded in a single parameter line of an
    Imfit configuration file).

    It holds the name, current value (e.g., a suggested initial value),
    possible lower and upper limits for fitting purposes, and whether or
    not the value is to be held fixed during a fit.

    Attributes
    ----------
        name : str
            label of the parameter (e.g., "X0", "sigma")

        value : float
            current value of the parameter

        limits : tuple of float
            lower and upper limits for parameter when fitting

        fixed : bool
            whether a parameter should be held fixed during fitting

    Methods
    -------
        setValue(value, vmin=None, vmax=None, fixed=False)
            Set the value (and limits, fixed state) of the parameter

        setTolerance(tol)
            Set the limits as +/- fraction of parameter value

        setLimitsRel(i1, i2)
            Set the limits as -i1,+i2 relative to parameter value

        setLimits(v1, v2)
            Set the limits directory

    """
    def __init__( self, name, value, vmin=None, vmax=None, fixed=False ):
        self._name = name
        self._limits = None
        self.setValue(value, vmin, vmax, fixed)


    @property
    def name(self):
        """
        The label of the parameter. Example: "x0", "I_e".
        """
        return self._name


    @property
    def value(self):
        """
        The value of the parameter.
        """
        return self._value


    @property
    def limits(self):
        """
        The limits of the parameter, as a tuple.
        """
        return self._limits


    def setValue( self, value, vmin=None, vmax=None, fixed=False ):
        """
        Set the value and constraints to the parameter.
        Note: both limits must be present at the same time.

        Parameters
        ----------
        value : float
            Value of the parameter.

        vmin : float OR 2-element sequence of float, optional
            Lower limit of the parameter.
            Default: ``None`` (= no limits).

            Alternately, this can be a two-element list, tuple, or Numpy
            array containing the lower and upper limits

        vmax : float, optional
            Upper limit of the parameter.
            Default: ``None`` ( = no limits).

        fixed : bool, optional
            Flag the parameter as fixed. Default: ``False``.
        """
        if vmin is not None:
            if vmax is None:
                try:
                    lower_limit, upper_limit = vmin
                except TypeError:
                    raise ValueError("If vmax is None, vmin must be None or two-element iterable.")
            else:
                lower_limit = vmin
                upper_limit = vmax
            # test for valid limits
            if value < lower_limit:
                lower_limit = value
            elif value > upper_limit:
                upper_limit = value
            if lower_limit >= upper_limit:
                raise ValueError("Lower limit must be < upper limit.")
            self._limits = (lower_limit, upper_limit)

        self._value = value
        self.fixed = fixed


    def setTolerance( self, tol ):
        """
        Set the limits using a fractional "tolerance" value, so that the
        lower limit = (1 - `tol`)*value and the upper limit = (1 + `tol`)*value.
        For example, a tolerance of 0.2 for a property of value 1.0
        sets the limits to [0.8, 1.2].

        Parameters
        ----------
        tol : float
            Fractional offset for lower and upper limits
            Must lie between ``0.0`` and ``1.0``.
        """
        if tol > 1.0 or tol < 0.0:
            raise ValueError('Tolerance must be between 0.0 and 1.0.')
        self._limits = (self._value * (1 - tol), self._value * (1 + tol))


    def setLimitsRel( self, i1, i2 ):
        """
        Set the limits using relative intervals. The limits
        will be [value - i1, value + i2]

        Parameters
        ----------
        i1 : float
            Lower limit interval.

        i2 : float
            Upper limit interval.
        """
        if i1 < 0.0 or i2 < 0.0:
            raise ValueError('Limit intervals must be positive.')
        self.setLimits(self._value - i1, self._value + i2)


    def setLimits( self, v1, v2 ):
        """
        Set the limits using absolute values: [v1, v2]

        Parameters
        ----------
        v1 : float
            Lower limit.

        v2 : float
            Upper limit.
        """
        if v1 >= v2:
            raise ValueError('v2 must be larger than v1.')
        if v1 > self._value:
            v1 = self._value
        elif v2 < self._value:
            v2 = self._value
        self._limits = (v1, v2)


    def __eq__(self, rhs):
        if ((self._name == rhs._name) and (self._value == rhs._value)
                    and (self._limits == rhs._limits)):
            return True
        else:
            return False


    def __str__(self):
        if self.fixed:
            return '{0:s}      {1:f}    fixed'.format(self._name, self._value)
        elif self.limits is not None:
            return '{0:s}      {1:f}    {2:f},{3:f}'.format(self._name, self._value, self._limits[0], self._limits[1])
        else:
            return '{0:s}      {1:f}'.format(self._name, self._value)



class FunctionDescription(object):
    """
    Holds information describing a single Imfit image function and its
    associated parameters, including their values and limits.

    It holds the official Imfit image-function name (e.g., "Gaussian",
    "EdgeOnDisk"), an optional label (e.g., "disk", "outer ring"), and a
    list of ParameterDescription objects which describe the parameter names,
    values, and limits (or fixed status) for each of the image function's
    parameters.

    Attributes
    ----------
        funcType : str
            name of the image function (e.g., "Gaussian", "EdgeOnDisk")

        name : str
            unique label for this function (e.g., "disk", "nuclear ring")

        _parameters : list of `ParameterDescription`
            the list of `ParameterDescription` objects for the image-function
            parameters

    Methods
    -------
        addParameter(p)
            Add a `ParameterDescription` instance for one of the function's
            parameter

        parameterList()
            Returns a list of the ParameterDescription objects

    """
    def __init__(self, func_type, name=None, parameters=None):
        if name is None:
            name = func_type
        self.funcType = func_type
        self._name = name
        self._parameters = []
        if parameters is not None:
            for p in parameters:
                self.addParameter(p)


    @property
    def name(self):
        """
        Custom name/label for the function (e.g., "disk", "nuclear ring").
        """
        return self._name


    def addParameter( self, p ):
        if not isinstance(p, ParameterDescription):
            raise ValueError('p is not a ParameterDescription object.')
        self._parameters.append(p)
        # add parameter names as attributes, so we can do things like
        # function_instance.<param_name>
        setattr(self, p.name, p)


    def parameterList(self):
        """
        A list of the parameters of this function.

        Returns
        -------
        param_list : list of :class:`ParameterDescription`
            List of the parameters.
        """
        return [p for p in self._parameters]


    def __eq__( self, rhs ):
        if ((self.funcType == rhs.funcType) and (self._name == rhs._name)
                    and (self._parameters == rhs._parameters)):
            return True
        else:
            return False


    def __str__(self):
        lines = []
        lines.append('FUNCTION {0}   # {1}'.format(self.funcType, self.name))
        lines.extend(str(p) for p in self._parameters)
        return '\n'.join(lines)


    def __deepcopy__(self, memo):
        f = FunctionDescription(self.funcType, self.name)
        f._parameters = [copy(p) for p in self._parameters]
        return f



class FunctionSetDescription(object):
    """
    Holds information describing an image-function block or set: one or more
    Imfit image functions sharing a common (X0,Y0) position on the image.

    It holds the X0 and Y0 coordinates, a list of FunctionDescription
    objects, and name or label for the function set (e.g., "fs0", "star 1",
    "galaxy 5", "offset nucleus", etc.)

    Attributes
    ----------

        name : str
            label of the parameter (e.g., "X0", "sigma")

        x0 : float
            x-coordinate of the function block/set's center

        y0 : float
            y-coordinate of the function block/set's center

        _functions : list of `FunctionDescription`
            the FunctionDescription objects, one for each image function

        name : str
            label of the parameter (e.g., "X0", "sigma")

    Methods
    -------
        addFunction(f)
            Add a FunctionDescription instance

        functionList()
            Returns a list of the FunctionDescription objects in the function
            block/set

        parameterList()
            Returns a list of ParameterDescription objects corresponding to
            the function block/set (including X0,Y0)

    """
    def __init__( self, name, x0param=None, y0param=None, functions=None ):
        self._name = name
        if x0param is None:
            self.x0 = ParameterDescription('X0', 0.0)
        else:
            self.x0 = x0param
        if y0param is None:
            self.y0 = ParameterDescription('Y0', 0.0)
        else:
            self.y0 = y0param
        self._functions = []
        if functions is not None:
            for f in functions:
                self.addFunction(f)


    @property
    def name(self):
        """
        Custom name/label for the function set.
        """
        return self._name


    def addFunction(self, f):
        """
        Add an Imfit image function created using :func:`function_description`.

        Parameters
        ----------
        f : :class:`FunctionDescription`.
            Function description to be added to the function set.
        """
        if not isinstance(f, FunctionDescription):
            raise ValueError('func is not a Function object.')
        if self._contains(f.name):
            raise KeyError('Function named %s already exists.' % f.name)
        self._functions.append(f)
        # add parameter names as attributes, so we can do things like
        # function_set_instance.<func_name>
        setattr(self, f.name, f)


    def _contains(self, name):
        for f in self._functions:
            if f.name == name:
                return True
        return False


    def functionList(self):
        """
        A list of the Imfit image-function types making up this function set.

        Returns
        -------
        function_list : list of strings
            List of the function types.
        """
        return [f.funcType for f in self._functions]


    def parameterList(self):
        """
        A list of all the parameters corresponding to this function set
        (including the X0,Y0 position).

        Returns
        -------
        param_list : list of :class:`ParameterDescription`
            List of the parameters.
        """
        params = []
        params.append(self.x0)
        params.append(self.y0)
        for f in self._functions:
            params.extend(f.parameterList())
        return params


    def __eq__(self, rhs):
        if ((self._name == rhs._name) and (self.x0 == rhs.x0) and (self.y0 == rhs.y0)
                    and (self._functions == rhs._functions)):
            return True
        else:
            return False


    def __str__(self):
        lines = []
        lines.append(str(self.x0))
        lines.append(str(self.y0))
        lines.extend(str(f) for f in self._functions)
        return '\n'.join(lines)


    def __deepcopy__(self, memo):
        fs = FunctionSetDescription(self._name)
        fs.x0 = copy(self.x0)
        fs.y0 = copy(self.y0)
        fs._functions = deepcopy(self._functions, memo)
        return fs



class ModelDescription(object):
    """
    Holds information describing an Imfit model for a particular image.

    The main components are a dict containing image-descriptions parameters
    and their values (e.g., {"GAIN": 4.5, "ORIGINAL_SKY": 325.39} and a list
    of FunctionSetDescription objects, corresponding to the image-function
    sets/blocks making up the model proper.

    Attributes
    ----------
        options : dict of {str: float}
            dict mapping image-description parameters (e.g., "GAIN") to
            their corresponding values

        _functionSets : list of `FunctionSetDescription`
            the individual image-function blocks/sets making up the model

    Class methods
    -------
        load(fname)
            Returns a new instance of this class based on a standard Imfit
            configuration file (`fname`).

    Methods
    -------
        addFunctionSet(fs)
            Add a function block/set to the model description

        functionSetIndices()
            Returns a list of ``int`` specifying the function-block start
            indices

        functionList()
            Retuns a list of FunctionDescription instances for all the
            image functions in the model

        parameterList()
            Returns a list of ParameterDescription instances corresponding
            to all the parameters in the model

    """

    def __init__( self, function_sets=None, options={} ):
        self.options = {}
        self.options.update(options)
        self._functionSets = []
        if function_sets is not None:
            for fs in function_sets:
                self.addFunctionSet(fs)


    @classmethod
    def load(cls, fname):
        """
        This is a convenience method to generate a ModelDescription object
        from a standard Imfit configuration file.

        Parameters
        ----------
        fname : string
            Path to the Imfit configuration file.

        Returns
        -------
        model : :class:`ModelDescription`
            The model description.

        See also
        --------
        parse_config_file
        """
        # note that we need to put this here, rather than at the top of
        # the module, to prevent circular-import errors (since config.py
        # depends on definitions in *this* file)
        from .config import parse_config_file

        return parse_config_file(fname)


    def addFunctionSet(self, fs):
        """
        Add a function set to the model description.

        Parameters
        ----------
        fs : :class:`FunctionSetDescription`
            Function set description instance.
        """
        if not isinstance(fs, FunctionSetDescription):
            raise ValueError('fs is not a FunctionSet object.')
        if self._contains(fs.name):
            raise KeyError('FunctionSet named %s already exists.' % fs.name)
        self._functionSets.append(fs)
        setattr(self, fs.name, fs)


    def _contains(self, name):
        for fs in self._functionSets:
            if fs.name == name:
                return True
        return False


    def functionSetIndices(self):
        """
        Returns the indices in the full parameters list corresponding
        to the starts of individual function sets/blocks.
        """
        indices = [0]
        for i in range(len(self._functionSets) - 1):
            functionsThisSet = self._functionSets[i].functionList()
            indices.append(len(functionsThisSet))
        return indices


    def functionList(self):
        """
        List of the function types composing this model, as strings.

        Returns
        -------
        func_list : list of string
            List of the function types.
        """
        functions = []
        for function_set in self._functionSets:
            functions.extend(function_set.functionList())
        return functions


    def parameterList(self):
        """
        A list of the parameters composing this model.

        Returns
        -------
        param_list : list of :class:`ParameterDescription`
            List of the parameters.
        """
        params = []
        for function_set in self._functionSets:
            params.extend(function_set.parameterList())
        return params


    def getRawParameters(self):
        """
        Returns a Numpy array of the ModelDescription's current parameter values

        Returns
        -------
        paramValues : ndarray of float
        """
        paramsList = self.parameterList()
        return np.array([p.value for p in paramsList])


    def getParameterLimits(self):
        """
        Returns a list containing lower and upper limits for all parameters in the model.

        Returns
        -------
        parameterLimits : list of 2-element tuples of float
            [(lower_limit, upper_limit)_1, (lower_limit, upper_limit)_2, ...]
        """
        paramsList = self.parameterList()
        return [p.limits for p in paramsList]


    def __eq__(self, rhs):
        if ((self.options == rhs.options) and (self._functionSets == rhs._functionSets)):
            return True
        else:
            return False


    def __str__(self):
        lines = []
        for k, v in list(self.options.items()):
            lines.append('%s	%f' % (k, v))
        lines.extend(str(fs) for fs in self._functionSets)
        return '\n'.join(lines)


# 	def __getattr__(self, attr):
# 		return self[attr]
# 	
# 	
# 	def __getitem__(self, key):
# 		if not isinstance(key, str):
# 			raise KeyError('FunctionSet must be a string.')
# 		for fs in self._functionSets:
# 			if key == fs.name:
# 				return fs
# 		raise KeyError('FunctionSet %s not found.' % key)


    def __deepcopy__(self, memo):
        model = type(self)()
        model._functionSets = deepcopy(self._functionSets, memo)
        return model




class SimpleModelDescription(ModelDescription):
    """
    Simple model with only one function set.

    Returns
    -------
    model : :class:`SimpleModelDescription`
        Empty model description.

    Examples
    --------
    TODO: Add example of SimpleModelDescription.

    See also
    --------
    ModelDescription
    """

    def __init__(self, inst=None):
        super(SimpleModelDescription, self).__init__()
        if isinstance(inst, ModelDescription):
            if len(inst._functionSets) != 1:
                raise ValueError('Original model must have only one function set.')
            self.addFunctionSet(copy(inst._functionSets[0]))
        elif inst is None:
            self.addFunctionSet(FunctionSetDescription('fs'))
        else:
            raise ValueError('Invalid type: %s' % type(inst))


    @property
    def x0(self):
        """
        X coordinate of the center of the model.
        Instance of :class:`ParameterDescription`.
        """
        return self._functionSets[0].x0


    @property
    def y0(self):
        """
        Y coordinate of the center of the model.
        Instance of :class:`ParameterDescription`.
        """
        return self._functionSets[0].y0


    def addFunction(self, f):
        """
        Add a function created using :func:`function_description`.

        Parameters
        ----------
        f : :class:`FunctionDescription`.
            Function description to be added to the model.
        """
        self._functionSets[0].addFunction(f)
# 		for p in f.parameterList():
# 			setattr(self, p.name, p)


    def addFunctionSet(self, fs):
        if len(self._functionSets) >= 1:
            raise Exception('Only one function set allowed.')
        super(SimpleModelDescription, self).addFunctionSet(fs)

# 	return [attr] from the first (only, really) FunctionSetDescription
    #    _name; name
    #    x0; y0
    #
    # so simple_model_desc.x0 should --> simple_model_desc.functionSets[0].x0
    def __getattr__(self, attr):
        return self._functionSets[0][attr]