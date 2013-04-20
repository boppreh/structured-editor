do
   local default_fcompval = function( value ) return value end
   function table.intsearch( t,value,fcompval )
      local fcompval = fcompval or default_fcompval
      local ilow,ihigh = 1,#t
      if not t[ilow] then return end
      local _ilow,_ihigh = fcompval( t[ilow] ),fcompval( t[ihigh] )
      while _ilow and _ilow < _ihigh do
         local pos = math.floor( (value-_ilow)*(ihigh-ilow)/(_ihigh-_ilow) ) + ilow
         if pos < ilow or pos > ihigh then return end
         local compval = fcompval( t[pos] )
         if value == compval then
            local tfound,num = { pos,pos },pos-1
            while value == fcompval( t[num] ) do
               tfound[1],num = num,num-1
            end
            num = pos+1
            while value == fcompval( t[num] ) do
               tfound[2],num = num,num+1
            end
            return tfound
         elseif value < compval then
            ihigh = pos-1
         else
            ilow = pos+1
         end
         _ilow,_ihigh = fcompval( t[ilow] ),fcompval( t[ihigh] )
      end
      if value == fcompval( t[ilow] ) then
         local tfound,num = { ilow,ilow },ilow+1
         while value == fcompval( t[num] ) do
            tfound[2],num = num,num+1
         end
         return tfound         
      end
   end
   function table.intsearchrev( t,value,fcompval )
      local fcompval = fcompval or default_fcompval
      local ilow,ihigh = 1,#t
      if not t[ilow] then return end
      local _ilow,_ihigh = fcompval( t[ilow] ),fcompval( t[ihigh] )
      while _ilow and _ilow > _ihigh do
         local pos = math.floor( (_ihigh-value)*(ihigh-ilow)/(_ihigh-_ilow) ) + ilow
         if pos < ilow or pos > ihigh then return end
         local compval = fcompval( t[pos] )
         if value == compval then
            local tfound,num = { pos,pos },pos-1
            while value == fcompval( t[num] ) do
               tfound[1],num = num,num-1
            end
            num = pos+1
            while value == fcompval( t[num] ) do
               tfound[2],num = num,num+1
            end
            return tfound
         elseif value > compval then
            ihigh = pos-1
         else
            ilow = pos+1
         end
         _ilow,_ihigh = fcompval( t[ilow] ),fcompval( t[ihigh] )
      end
      if value == fcompval( t[ilow] ) then
         local tfound,num = { ilow,ilow },ilow+1
         while value == fcompval( t[num] ) do
            tfound[2],num = num,num+1
         end
         return tfound         
      end
   end
end
