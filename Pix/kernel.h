#ifndef KERNEL_H
#define KERNEL_H

// kernel handles all the control logic
// it is a singleton
class Kernel
{
public:

    ~Kernel();
    static Kernel* getInstance() {
        return Kernel::instance;
    }

private:

    Kernel();
    static Kernel* instance;

};

#endif // KERNEL_H
