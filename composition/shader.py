import re
import os
import os.path



# --------------------------------------------------- ShaderException class ---
class ShaderException(Exception): pass



# ------------------------------------------------------------ Shader class ---
class Shader(object):
    """
    """

    # ---------------------------------
    def __init__(self, source=""):
        if os.path.exists(source):
            with open(source) as file:
                self._source = file.read()
        else:
            self._source = source
        self.parse()


    # ---------------------------------
    def parse(self):
        """
        Try to parse shader source into known entities
        """

        code = self._source
        code = self.get_uniforms(code)
        code = self.get_attributes(code)
        code = self.get_varyings(code)
        code = self.get_functions(code)
        code = '\n'.join([line for line in code.splitlines() if line.strip()])
        self._unknown = code
        

    # ---------------------------------
    def get_uniforms(self, code):
        """
        Extract uniforms (name and type)
        """

        self._uniforms = []
        regex = re.compile('\s*uniform\s+(?P<type>\w+)\s+(?P<name>\w+)\s*;')
        m = re.search(regex,code)
        while m:
            self._uniforms.append((m.group('name'), m.group('type')))
            code = code[:m.start()] + code[m.end():]
            m = re.search(regex,code)
        return code

    # ---------------------------------
    def get_attributes(self, code):
        """
        Extract attributes (name and type)
        """

        self._attributes = []
        regex = re.compile('\s*attribute\s+(?P<type>\w+)\s+(?P<name>\w+)\s*;')
        m = re.search(regex,code)
        while m:
            self._attributes.append((m.group('name'), m.group('type')))
            code = code[:m.start()] + code[m.end():]
            m = re.search(regex,code)
        return code


    # ---------------------------------
    def get_varyings(self, code):
        """
        Extract varyings  (name and type)
        """

        self._varyings = []
        regex = re.compile('\s*varying\s+(?P<type>\w+)\s+(?P<name>\w+)\s*;')
        m = re.search(regex,code)
        while m:
            self._varyings.append((m.group('name'), m.group('type')))
            code = code[:m.start()] + code[m.end():]
            m = re.search(regex,code)
        return code


    # ---------------------------------
    def get_functions(self, code):
        """
        Extract functions (name, return type, args and code)
        """

        self._functions = []
        regex = re.compile("""(?P<rtype>\w+)\s+"""
                           """(?P<name>\w+)\s*"""
                           """\((?P<args>.*?)\)\s*"""
                           """\{(?P<code>.*?)\}""", re.DOTALL)
        m = re.search(regex,code)
        while m:
            if m.group('name') == 'main':
                self._main = m.group('code')
            else:
                self._functions.append( (m.group('name'), m.group('rtype'),
                                         m.group('args'), m.group('code')) )
            code = code[:m.start()] + code[m.end():]
            m = re.search(regex,code)

        return code
 

    # ---------------------------------
    def __repr__(self):

        r = ""

        r += "// --- unknown section ---\n"
        r += self._unknown + '\n'
        r += "\n"

        r += "// --- uniform section ---\n"
        for (name,utype) in self._uniforms:
            r+= "uniform %s %s;\n" % (utype,name)
        r += '\n'

        r += "// --- attribute section ---\n"
        for (name,atype) in self._attributes:
            r+= "attribute %s %s;\n" % (atype,name)
        r += '\n'

        r += "// --- varying section ---\n"
        for (name,vtype) in self._varyings:
            r+= "varying %s %s;\n" % (vtype,name)
        r += '\n'

        r += "// --- functions ---\n"
        for (name,rtype,args,code) in self._functions:
            r+= "%s %s(%s)\n{\n %s \n}\n\n" % (rtype,name,args,code)

        r += "// --- main ---\n"
        r += "void main()\n{\n %s \n}\n\n" % self._main

        return r



    # ---------------------------------
    def add_variable(self, qualifier, name, dtype):
        """
        """
        
        if qualifier == 'uniform':
            vars   = self._uniforms 
            names  = [n for (n,t) in self._uniforms]
            others = [n for (n,t) in self._attributes+self._varyings]
        elif qualifier == 'attribute':
            vars   = self._attributes
            names  = [n for (n,t) in self._attributes]
            others = [n for (n,t) in self._uniforms+self._varyings]
        elif qualifier == 'varying':
            vars   = self._varyings
            names  = [n for (n,t) in self._varyings]
            others = [n for (n,t) in self._uniforms+self._attributes]
        else:
            raise(ShaderException, "Unknown qualifier (%s)" % qualifier)

        if name in others:
            raise(ShaderException,
                  "A different variable with that name (%s) exists" % name)
        elif name in names:
            index = names.index(name)
            if vars[index][1] != dtype:
                raise(ShaderException,
                      "A variable with same name (%s) and different type (%s) exists"  % (name,dtype))
            else:
                # this mean the variable is already in the list
                # No need to add it
                pass
        else:
            vars.append( (name,dtype) )


    # ---------------------------------
    def add_function(self, name, rtype, args, code):
        
        names = [n for (n,r,a,c) in self._functions]

        # A function with the same name already exists
        if name in names:
            # Same arguments
            if args.replace(' ','') == a.replace(' ',''):
                if( r != rtype ):
                    raise(ShaderException,
                          "A function with a different return type (%s) exists" % r)
                else:
                    # this mean the function is already in the list
                    # No need to add it
                    pass
            # Different argument, we add the overloaded function
            else:
                self._functions.append( (name,rtype,args,code) )
        # No function with that name
        else:
            # We add it
            self._functions.append( (name,rtype,args,code) )
                
                    

    # ---------------------------------
    def __add__(self, other):

        # 1. Merge uniforms
        for (name,dtype) in other._uniforms:
            self.add_variable('uniform', name, dtype)

        # 2. Merge attributes
        for (name,dtype) in other._attributes:
            self.add_variable('attribute', name, dtype)

        # 3. Merge varyings
        for (name,dtype) in other._varyings:
            self.add_variable('varying', name, dtype)

        # 4. Merge unknown code
        self._unknown += '\n'+other._unknown

        # 5. Merge functions
        for (name,rtype,args,code) in other._functions:
            self.add_function(name, rtype, args, code)

        # 6. Merge main
        self._main += '\n' + other._main
        
        return self


# -----------------------------------------------------------------------------

source1 = """
uniform   vec4 u_uniform;
attribute vec4 a_attribute;
varying   vec4 v_varying;
void main() { /* main */ }
"""

source2 = """
uniform float u_uniform;
void main() { /* main  */ }
"""

source3 = """
varying vec4 u_uniform;
void main() { /* main */ }
"""

source4 = """
uniform vec4 u_uniform1;
void main() { /* main */ }
"""


# shader = Shader(source1)+Shader(source1) # ok
# shader = Shader(source1)+Shader(source2) # exception
# shader = Shader(source1)+Shader(source3) # exception
shader = Shader(source1)+Shader(source4) # ok

print(shader)
