#ifndef INJECTOR_HPP
#define INJECTOR_HPP

#include "ros/ros.h"
#include <ros/package.h>

#include "archlib/Uncertainty.h"
#include "archlib/ROSComponent.hpp"

class Injector : public arch::ROSComponent {

	public:
    	Injector(int &argc, char **argv, const std::string &name);
    	virtual ~Injector();

    private:
      	Injector(const Injector &);
    	Injector &operator=(const Injector &);

	public:
		virtual void setUp();
		virtual void tearDown();
		virtual void body();

		void injectUncertainty(const std::string &component, const std::string &content);

	private:
		ros::NodeHandle handle;
		int cycles;
		double noise_factor;
};

#endif 