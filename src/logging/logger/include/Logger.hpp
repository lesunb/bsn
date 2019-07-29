#ifndef LOGGER_HPP
#define LOGGER_HPP

#include <fstream>
#include <iostream>
#include <chrono>

#include "ros/ros.h"
#include <ros/package.h>

#include "messages/Status.h"
#include "messages/Event.h"

class Logger {

	public:
    	Logger(int &argc, char **argv, std::string);
    	virtual ~Logger();

		void setUp();
		void run();

    private:
      	Logger(const Logger &);
    	Logger &operator=(const Logger &);

		std::string now() const;

  	public:
	  	void receiveStatus(const messages::Status::ConstPtr& /*msg*/);
	  	void receiveEvent(const messages::Event::ConstPtr& /*msg*/);


  	private:
		std::fstream fp;
		std::string filepath;
		int32_t logical_clock;

		ros::Publisher status_logger2manager_pub, event_logger2manager_pub;
};

#endif 