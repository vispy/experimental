
CALL_TEMPATE = '// CALL:'

from collections import OrderedDict


class Function(object):
    """ Simple function object for composing GLSL snippets
    
    Each function consists of a GLSL snipped in the form of a GLSL
    function. The code may have stub variables that start with the
    dollar sign by convention. These stubs can be replaced with calls
    to other functions (or with plain source code), using the index
    operation.
    
    To "finalize" a function (i.e. apply the replacements), you call
    it. This returns a new function object, and in principle you can
    apply more replacements. To get the final source code, just convert
    to string.
    
    In a call to a function, you can specify arguments (function objects
    or plain text), which will be used as arguments in the function call.
    
    Example
    -------
    
        code = Template()
        code['$position'] = Trasform1(Transform2(Transform3(Position())
        code['$some_stub'] = 'vec2(3.0, 1.0)'
        # You can actually change any code you want, but use this with care!
        code['gl_FragColor = color;'] = 'gl_FragColor = vec4(color.rgb, 0.5)'
    
    Things to consider / work out
    -----------------------------
    
    * Maybe it should be possible to rename a function, because sometimes you
      may want to use a function for different purposes. I think 
      ``SomeFunction(name='new_name')`` should work.
    * There should be a way to easily set values to varyings. Maybe we need
      a post-hook and a pre-hook or something.
    
    """
    def __init__(self, code, name=None, dependencies=None):
        self._code = code.strip()
        
        # Stuff we need to replace code
        self._replacements = OrderedDict()
        self._dependencies = set(dependencies or [])
        
        # We keep track of how we want to be called
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
                #self._arg = line.split(' ',1)[1].split('(')[1].split(')')[0]
                line = line.split('//')[0].rstrip() + ' ' + CALL_TEMPATE
                self._replacements[CALL_TEMPATE] = CALL_TEMPATE + ' ()'
            lines.append(line)
        # Store
        self._name = name
        self._code = '\n'.join(lines)
        # Set replacements for uniforms and attributes
        # todo: EEK! only do whole worlds, with regexp. 
        for line in lines:
            if line.startswith('uniform'):
                uname = line.split(' ')[2].strip(' ;')
                self._replacements[uname] = self.uniform(uname)
            elif line.startswith('attribute'):
                aname = line.split(' ')[2].strip(' ;')
                self._replacements[aname] = self.attribute(aname)
     
    def _convert(self):
        """ Apply the replacements. Return new code string.
        """
        code = self._code
        for key, val in self._replacements.items():
            code = code.replace(key, val)
        code += '\n'
        
        for dep in self._dependencies:
            code += '\n'
            code = code + str(dep)
        
        return code.rstrip() + '\n'
    
    def __repr__(self):
        return "<Function '%s' at %s>" % (self.name, str(id(self)))
        
    def __str__(self):
        return self._convert()
    
    def new(self, name=None):
        """ Make a copy of this Function object, discarting any
        replacements and function signature. Optionally the name of the
        function can be reset.
        """
        return Function(self._code, name=name)
    
    def apply(self, name=None):
        """ Create a new Function object that consists of the current
        one with all replacements applied. Optionally the name of the
        function can be reset.
        """
        return Function(str(self), name=name)
    
    @property
    def name(self):
        """ The function name.
        """
        return self._name
    
    @property
    def call_line(self):
        """ The line of code used to call this function.
        """
        try:
            sig = self._replacements[CALL_TEMPATE].split(':')[1].strip()
        except KeyError:
            sig = '()'
        return self._name + sig
    
    def uniform(self, uname):
        """ Get mangled uniform name given the initial name.
        """
        return uname + '__' + self._name
        #return self._replacements[uname]
    
    def attribute(self, aname):
        """ Get mangled attribute name given the initial name.
        """
        return aname + '__' + self._name
        #return self._replacements[aname]
    
    def __setitem__(self, key, val):
        """ Setting of replacements through a dict-like syntax. Replacements
        can be verbatim code and Function objects.
        """
        if key not in self._code:
            raise ValueError('Could not find %r in code of %r' % (key, self))
        assert isinstance(key, str)
        
        if isinstance(val, Function):
            self._replacements[key+'('] = val.name + '('
            self._replacements[key] = val.call_line
            self._dependencies.add(val)
        elif isinstance(val, str):
            self._replacements[key] = val
        else:
            raise ValueError('Dont know how to inject %r' % val)
    
    def __call__(self, *args, **kwargs):
        """ Set the signature for this function. Each argument can be
        verbatim code or a Function object.
        """
        name = kwargs.pop('name', None)
        if kwargs:
            raise ValueError('Invalid arguments: %r' % list(kwargs.keys()))
        str_args = []
        for arg in args:
            if isinstance(arg, Function):
                str_args.append(arg.call_line)
                self._dependencies.add(arg)
            elif isinstance(arg, str):
                str_args.append(arg)
            else:
                raise ValueError('Dont know how to inject %r' % val)
        s = ', '.join(str_args)
        self._replacements[CALL_TEMPATE] = CALL_TEMPATE + ' (%s)' % s
        return self
        #self._convert()
        #fun = self
        #return Function(fun._final_code, self._dependencies, args)
    
    
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
uniform float u_zoffet;
vec4 transform_zoffset(vec4 pos)
{
    pos.z += u_zoffet;
    return pos;
}
""")

Frag_template = Function("""
void main (void)
{
    int nlights = $nlights;
    vec4 pos = $position;
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
code['$endtransform'] = t4()
code['$nlights'] = '4'

# Show result
print(code)

# Yay, we can easil obtain the uniform names via their original function object
print(t1.uniform('u_scale'), t3.uniform('u_scale'))