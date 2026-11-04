#pragma once
#include <atomic>
namespace node {
enum class MaintenanceOwner { None, Ota, Storage };
struct MaintenanceGate {
    std::atomic<MaintenanceOwner> owner{MaintenanceOwner::None};
    bool claim(MaintenanceOwner wanted) {
        if(wanted==MaintenanceOwner::None) return false;
        auto expected=MaintenanceOwner::None;
        return owner.compare_exchange_strong(expected,wanted);
    }
    void release(MaintenanceOwner held) {
        owner.compare_exchange_strong(held,MaintenanceOwner::None);
    }
};
}
