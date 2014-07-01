"""
Implementation of a simple function object for re-using and composing
GLSL snippets. See the docstring of Function for considerations.

There is some example code at the bottom. Just run this script and play
with it!

Details
-------

Each function object keeps track of a dict of replacments and a set
of dependencies. When composing the final code, the dependencies 
are collected recursively and then the replacements are applied
on the code of each function object, using the known replacements
of that object only. In effect, replacements are local to a Function
object, and they can be applied after composing the Function object
together.

To set signatures, the Function object can be called. At that moment,
any dependencies are added and the resulting string signature is stored
on the Function object. Generally, this signature will be used as part
of a replacement string: ``code['$position'] = trans(position())``.
Thus the local storage of the signature string is only temporary to
communicate the signature downstream. In effect, we can reuse a function
without having to worry about signature mixup.

Things to consider / work out
-----------------------------

* Stuff to find names and attriutes/uniforms needs to be made more robust
  using regexp; I am not so good with regexp :(
* There should be a way to easily set values to varyings. Maybe we
  just need a convention for a a post-hook and a pre-hook or
    something.
* ``code = SomeFunction.new()`` or ``code = Function(SomeFunction)``?
  Both work actually. new() seems nice and short, but maybe the latter
  is more Pythonic.
    
    
"""

from collections import OrderedDict


class Function(object):
    """ Simple function object for re-using and composing GLSL snippets
    
    Each Function consists of a GLSL snipped in the form of a GLSL
    function. The code may have stub variables that start with the
    dollar sign by convention. These stubs can be replaced with calls
    to other functions (or with plain source code), using the index
    operation. 
    
    The signature of a function can be set by calling the Function
    object, arguments can be verbatim code or Function objects. Note
    that if the signature is already specified in the template code,
    that signature is used.
    
    To get the final source code, simply convert the Function object
    to str (or print it). In order to further modify a 'finished'
    Function object, firts turn it into a 'fresh' Function via
    ``Function(str(fun))``.
    
    Example
    -------
        
        # ... omitted deinition of FragShaderTemplate and ScaleTransform
        
        # Always create new Function objects to ensure they are 'fresh'.
        # You can also give the function a new name here.
        code = FragShaderTemplate.new()
        trans1 = ScaleTransform.new('trans1')
        trans2 = ScaleTransform.new('trans2')
        position = Position()
        
        # Compose the different components
        code['$position'] = trans1(trans2(position())
        code['$some_stub'] = 'vec2(3.0, 1.0)'
        
        # You can actually change any code you want, but use this with care!
        code['gl_FragColor = color;'] = 'gl_FragColor = vec4(color.rgb, 0.5)'
        
        # By renaming a Function object, the attribute/uniform names are
        # mangled to avoid name conflicts. It is easy to retieve the original
        # names:
        trans1_scale_name = trans1.uniform('u_scale')
        trans2_scale_name = trans1.uniform('u_scale')
        
    """
    def __init__(self, code, name=None):
        
        # Get and strip code
        if isinstance(code, Function):
            code = code._code
        self._code = code.strip()
        
        # Stuff we need to replace code
        self._replacements = OrderedDict()
        self._dependencies = OrderedDict()  # We use it as an ordered set
        
        # Variable to communicate the signature 'downstream'
        self._sig = '()'
        
        # Prepare: get name, inject CALL_TEMPLATE, set replacements for
        # uniforms/attributes
        self._prepare(name)
    
    def _prepare(self, newname=None):
        """ Get name of function and prepare code a bit to our format.
        """
        # Try to get name. This needs to be made more robust!
        name = ''
        lines = []
        for line in self._code.splitlines():
            if (not name) and '(' in line:
                name = line.split(' ',1)[1].split('(')[0].strip()
                if newname:
                    newname = newname.replace('{id}', hex(id(self)))
                    line = line.replace(name, newname)
                    name = newname
            lines.append(line)
        # Store
        self._name = name
        self._code = '\n'.join(lines)
        # If object is renamed, set replacements for uniforms and attributes
        # todo: EEK! only do whole worlds, with regexp. 
        if newname:
            for line in lines:
                if line.startswith('uniform'):
                    uname = line.split(' ')[2].strip(' ;')
                    self._replacements[uname] = self.uniform(uname)
                elif line.startswith('attribute'):
                    aname = line.split(' ')[2].strip(' ;')
                    self._replacements[aname] = self.attribute(aname)
     
    def _get_replaced_code(self):
        """ Return code, with replacements applied.
        """
        code = self._code
        # First apply replacements; they are applied only for this function
        for key, val in self._replacements.items():
            code = code.replace(key, val)
        return code
    
    def _get_all_dependencies(self):
        """ Get all dependencies (recursive) for this Function object.
        """
        deps = OrderedDict()
        for dep in self._dependencies:
            deps[dep] = None
            deps.update(dep._get_all_dependencies())
        return deps
    
    def _convert(self):
        """ Apply the replacements and add code for dependencies.
        Return new code string.
        """
        # todo: we need to prepend the function definitions here
        
        # Add our code
        code = self._get_replaced_code()
        # Add code for dependencies
        for dep in self._get_all_dependencies():
            code += '\n\n'
            code += dep._get_replaced_code()
        # Done
        return code.rstrip() + '\n'
        
    def __repr__(self):
        return "<Function '%s' at %s>" % (self.name, str(id(self)))
        
    def __str__(self):
        return self._convert()
    
    def new(self, name=None):
        """ Make a copy of this Function object, discarting any
        replacements and function signature. 
        
        Optionally the name of the function can be reset. If this is
        done, the attributes and uniform names are mangled with the
        given name as well. Use the uniform() and attribute() methods
        to get the real names.
        
        """
        return Function(self._code, name=name)
    
    @property
    def name(self):
        """ The function name.
        """
        return self._name
    
    def uniform(self, uname):
        """ Get mangled uniform name given the initial name.
        """
        return uname + '__' + self._name
    
    def attribute(self, aname):
        """ Get mangled attribute name given the initial name.
        """
        return aname + '__' + self._name
    
    def __setitem__(self, key, val):
        """ Setting of replacements through a dict-like syntax. Replacements
        can be verbatim code and Function objects.
        """
        if key not in self._code:
            raise ValueError('Could not find %r in code of %r' % (key, self))
        assert isinstance(key, str)
        
        if isinstance(val, Function):
            self._replacements[key+'('] = val.name + '('
            self._replacements[key] = val.name + val._sig
            self._dependencies[val] = None
        elif isinstance(val, str):
            self._replacements[key] = val
        else:
            raise ValueError('Dont know how to inject %r' % val)
    
    def __call__(self, *args, **kwargs):
        """ Set the signature for this function and return this Function
        object. Each argument can be verbatim code or a Function object.
        """
        name = kwargs.pop('name', None)
        if kwargs:
            raise ValueError('Invalid arguments: %r' % list(kwargs.keys()))
        str_args = []
        for arg in args:
            if isinstance(arg, Function):
                str_args.append(arg.name+arg._sig)
                self._dependencies[arg] = None
            elif isinstance(arg, str):
                str_args.append(arg)
            else:
                raise ValueError('Dont know how to inject %r' % val)
        self._sig = '(%s)' % ', '.join(str_args)
        return self
    
    
##


Position = Function("""
attribute vec4 a_position;
vec4 position()
{   
    return a_position;
}
""")

TransformScale = Function("""
uniform float u_scale;
vec4 transform_scale(vec4 pos)
{
    pos.xyz *= u_scale;
    return pos;
}
""")

TransformZOffset = Function("""
vec4 transform_zoffset(vec4 pos)
{
    pos.z += $offset;
    return pos;
}
""")

Frag_template = Function("""
void main (void)
{
    int nlights = $nlights;
    vec4 pos = $position;
    pos += $correction;
    gl_Position = $endtransform(pos);
}

""")



# Get function objects. Generate random name for transforms
code = Frag_template.new()
position = Position.new()
t1 = TransformScale.new('trans'+str(1))
t2 = TransformZOffset.new('trans'+str(2))
t3 = TransformScale.new('trans'+str(3))
t4 = TransformScale.new()

# Compose everything together
code['$position'] = t1(t2(t3(position())))
code['$correction'] = t1(position())  # Look, we use t1 again, different sig
code['$endtransform'] = t4()  # Sig defined in template overrides given sig
code['$nlights'] = '4'

t2['$offset'] = '1.0'  # We can assign replacements after combining them

# Show result
print(code)

# Yay, we can easil obtain the uniform names via their original function object
print(t1.uniform('u_scale'), t3.uniform('u_scale'))
