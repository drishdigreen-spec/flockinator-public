#pragma once
#include "vendor/json.hpp"
#ifdef ESP_PLATFORM
#include "esp_heap_caps.h"
template<class T> struct external_allocator {
    using value_type=T;
    external_allocator()=default;
    template<class U> external_allocator(const external_allocator<U>&) {}
    T* allocate(size_t n){auto* p=heap_caps_malloc(n*sizeof(T),MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);if(!p)abort();return static_cast<T*>(p);}
    void deallocate(T* p,size_t){heap_caps_free(p);}
    template<class U> bool operator==(const external_allocator<U>&)const{return true;}
    template<class U> bool operator!=(const external_allocator<U>&)const{return false;}
};
using Json=nlohmann::basic_json<std::map,std::vector,std::string,bool,int64_t,uint64_t,double,external_allocator>;
#else
using Json=nlohmann::json;
#endif
using std::string;
inline string unit_label(int i){char b[]={char('A'+i%4),char('1'+i/4),0};return b;}
inline bool natural(const Json& v,uint64_t hi){
    return (v.is_number_unsigned()&&v.get<uint64_t>()<=hi)||
           (v.is_number_integer()&&v.get<int64_t>()>=0&&uint64_t(v.get<int64_t>())<=hi);
}
