import string

class MyFmt(string.Formatter):
    # def convert_field(self, value, conversion):
    #     if conversion[0] == '=':
    #         return "default"
    #     else:
    #         return string.Formatter.convert_field(self, value, conversion)

    def format_field(self, value, format_spec):
        if format_spec:
            if format_spec[0] == '~' or format_spec[0] == '=':
                if value:
                    return str(value) 
                else:
                    return format_spec[1:]
            elif format_spec[0] == '+':
                if value:
                    return format_spec[1:] + str(value)
            elif format_spec[0] == '-':
                dep = format_spec[1:]
                if dep in self.kwargs:
                    return str(value)
                else:
                    return ''
        
        return string.Formatter.format_field(self, value, format_spec)

    def vformat(self, format_string, args, kwargs):
        self.format_string = format_string
        self.args = args
        self.kwargs = kwargs

        return string.Formatter.vformat(self, format_string, args, kwargs)

a = MyFmt().format("{a}\t{b:~}\t{c:-d}", a=1, b=20, c=3)
print(a)