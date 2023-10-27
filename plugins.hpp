#ifndef PLUGINS_HPP
#define PLUGINS_HPP

class Base_Soma {
public:
	Base_Soma(){}
    virtual ~Base_Soma(){}
	virtual double update_soma(double input) = 0;
};

typedef Base_Soma* _create_soma();
typedef void _destroy_soma(Base_Soma*);

void init_soma();

extern _create_soma* create_soma;
extern _destroy_soma* destroy_soma;

#endif