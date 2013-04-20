BaseObject = {
  super   = nil,
  name    = "Object",
  new     =
    function(class)
      local obj  = {class = class}
      local meta = {
        __index = function(self,key) return class.methods[key] end 
      }            
      setmetatable(obj,meta)
      return obj
    end,
  methods = {classname = function(self) return(self.class.name) end},
  data    = {}
}

function setclass(name, super)
  if (super == nil) then
    super = BaseObject
  end

  local class = {
    super = super; 
    name  = name; 
    new   =
      function(self, ...) 
        local obj = super.new(self, "___CREATE_ONLY___");
        if (super.methods.init) then
          obj.init_super = super.methods.init
        end

	if (self.methods.init) then
            if (tostring(arg[1]) ~= "___CREATE_ONLY___") then
              obj.init = self.methods.init
              if obj.init then
                obj:init(unpack(arg))
              end
            end
	end

        return obj
      end,  
    methods = {}
  }

  setmetatable(class, {
    __index = function(self,key) return self.super[key] end,
    __call  = function(self,...) return self.new(self,unpack(arg)) end 
  })

  setmetatable(class.methods, {
    __index = function(self,key) return class.super.methods[key] end
  })
  return class
end    
