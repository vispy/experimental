
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
    def __init__(self, code, dependencies=None, inargs=None):
        self._code = code
        
        # Try to get name. This needs to be made more robust!
        self._name = ''
        self._arg = ''
        for line in code.splitlines():
            if '(' in line:
                self._name  = line.split(' ',1)[1].split('(')[0]
                self._arg = line.split(' ',1)[1].split('(')[1].split(')')[0]
        self._name = self._name.strip()
        self._arg = self._arg.strip()
        
        self._inargs = inargs or []
        self._final_code = ''
        self._replacements = {}
        self._dependencies = set(dependencies or [])
    
    
    @property
    def name(self):
        """ The function name.
        """
        return self._name
    
    @property
    def call_line(self):
        
        #argname = '$' + self._arg.split(' ')[1]
        #argname = '$%s_%s' % (self.name, self._arg.split(' ')[1])
        args = []
        for arg in self._inargs:
            if isinstance(arg, Function):
                args.append(arg.call_line)
                self._dependencies.add(arg)
            elif isinstance(arg, str):
                args.append(arg)
            else:
                raise ValueError('Dont know how to inject %r' % val)
        s = ', '.join(args)
        return '%s(%s)' % (self.name, s)
    
    def __setitem__(self, key, val):
        if key not in self._code:
            raise ValueError('Could not find %r in code of %r' % (key, self))
        assert isinstance(key, str)
        
        if isinstance(val, Function):
            # todo: what about args?
            self._replacements[key] = val.call_line
            self._dependencies.add(val)
        elif isinstance(val, str):
            self._replacements[key] = val
        else:
            raise ValueError('Dont know how to inject %r' % val)
    
    def __call__(self, *args):
        self._convert()
        fun = self
        return Function(fun._final_code, self._dependencies, args)
    
    
    def _convert(self):
        code = self._code
        for key, val in self._replacements.items():
            code = code.replace(key, val)
        
        for dep in self._dependencies:
            code += '\n'
            code = code + str(dep)
            
        self._final_code = code.strip() + '\n'
    
    def __repr__(self):
        return "<Function '%s' at %s>" % (self.name, str(id(self)))
        
    def __str__(self):
        self._convert()
        return self._final_code
    


##

Normal = Function("""
vec4 normal(vec4 pos)
{
    ... do some magic
    return pos;
}
""")


Position = Function("""
attribute vec4 a_position;

vec4 position()
{   
    return a_position;
{

""")

Transform = Function("""
vec4 transform(vec4 pos)
{
    pos.z += 1;
    return pos;
}
""")


Frag_template = Function("""
void main (void)
{
    int nlights = $nlights;
    gl_Position = $position;
}

""")



code = Frag_template()
code['$position'] = Transform(Position())
code['$nlights'] = '4'

print(code)



