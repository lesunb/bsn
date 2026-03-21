#include "libbsn/configuration/SensorConfiguration.hpp"

using namespace std;
using namespace bsn::range;

namespace bsn {
	namespace configuration {
		SensorConfiguration::SensorConfiguration():
			id(),
			lowRisk(),
			mediumRisk(),
			highRisk(),
			lowPercentage(),
			midPercentage(),
			highPercentage() {}

		SensorConfiguration::SensorConfiguration(int32_t i, Range l, 
			array<Range, 2> m, array<Range, 2> h, array<Range, 3> p) : 
			id(i),
			lowRisk(l),
			mediumRisk(m),
			highRisk(h),
			lowPercentage(p[0]),
			midPercentage(p[1]),
			highPercentage(p[2]) {}

		SensorConfiguration::SensorConfiguration(const SensorConfiguration &obj) : 
			id(obj.getId()),
			lowRisk(obj.getLowRisk()),
			mediumRisk(obj.getMediumRisk()),
			highRisk(obj.getHighRisk()),
			lowPercentage(obj.getLowPercentage()),
			midPercentage(obj.getMidPercentage()),
			highPercentage(obj.getHighPercentage()) {}

		SensorConfiguration& SensorConfiguration::operator=(const SensorConfiguration &obj) {
            id = obj.getId();
            lowRisk = obj.getLowRisk();
            mediumRisk = obj.getMediumRisk();
			highRisk = obj.getHighRisk();
			lowPercentage = obj.getLowPercentage();
			midPercentage = obj.getMidPercentage();
			highPercentage = obj.getHighPercentage();        
            return (*this);
        }

		int32_t SensorConfiguration::getId() const {
			return this->id;
		}

		void SensorConfiguration::setId(const int32_t id) {
			this->id = id;
		}

		// Retorna o quão deslocado do meio um valor está
		double SensorConfiguration::getDisplacement(Range range, double number, string logic = "crescent") {
			// Crescent indica o quão deslocado um elemento está do começo
			// inverse indica o quão deslocado um elemento está do fim
			// medium indica o quão deslocado um elemento está do meio
			double lb = range.getLowerBound();
			double ub = range.getUpperBound();
			double result;

			if(logic == "decrescent") {
				result = fabs(number - ub);
				result /= (ub - lb);
			}
			else if(logic == "crescent") {
				result = number - lb;
				result /= (ub - lb);
			}
			else if(logic == "medium") {				
				double mediumValue = (ub + lb)/2.0;				
				result = fabs(number - mediumValue);
				result /= (ub - mediumValue);
						
			}
			else { 
				throw std::invalid_argument("Invalid operation given to getDisplacement");
				result = -1;
			}

			return result;
		}

		double SensorConfiguration::convertRealPercentage(Range newRange, double number) {
			Range oldRange(0.0, 1.0);
			double lb = newRange.getLowerBound();
			double ub = newRange.getUpperBound();
			
			return oldRange.convert(lb,ub,number);
		}

		double SensorConfiguration::evaluateNumber(double number) {
			double displacement;
			Range per_cent(0,100);

			if(lowRisk.in_range(number)) {				
				displacement = getDisplacement(lowRisk, number, "medium");
				return convertRealPercentage(lowPercentage, displacement);
			}	

			else if(mediumRisk[0].in_range(number)) {
				displacement = getDisplacement(mediumRisk[0], number, "decrescent");	
				return convertRealPercentage(midPercentage, displacement);	
			}

			else if(mediumRisk[1].in_range(number)) {
				displacement = getDisplacement(mediumRisk[1], number);
				return convertRealPercentage(midPercentage, displacement);	
			}

			else if(highRisk[0].in_range(number)) {
				displacement = getDisplacement(highRisk[0], number, "decrescent");
				return convertRealPercentage(highPercentage, displacement);			
			}

			else if(highRisk[1].in_range(number)) {
				displacement = getDisplacement(highRisk[1], number);		
				return convertRealPercentage(highPercentage, displacement);	
			}
			else {
				return -1;
			}	
		}

		const string SensorConfiguration::toString() {
			stringstream sstr;

			sstr << "Sensor id(" << id << ") with ranges: " << endl;
			sstr << "Low: " << lowRisk.to_print() << endl;
			sstr << "Medium: " << mediumRisk[0].to_print() << mediumRisk[1].to_print() << endl;
			sstr << "High: " << highRisk[0].to_print() << highRisk[1].to_print() << endl;

			sstr << endl;

			return sstr.str();

		}

		Range SensorConfiguration::getLowRisk() const {
			return lowRisk;
		}

		void SensorConfiguration::setLowRisk(const Range l) {
			lowRisk = l;
		}

		array<Range, 2> SensorConfiguration::getMediumRisk() const {
			return mediumRisk;
		}

		void SensorConfiguration::setMediumRisk(const array<Range, 2> m) {
			mediumRisk = m;
		}

		array<Range, 2> SensorConfiguration::getHighRisk() const {
			return highRisk;
		}

		bool SensorConfiguration::isLowRiskPercentage(double val) {
			return lowPercentage.in_range(val);
		}

		bool SensorConfiguration::isMidRiskPercentage(double val) {
			return midPercentage.in_range(val);
		}

		bool SensorConfiguration::isHighRiskPercentage(double val) {
			return highPercentage.in_range(val);
		}

		bool SensorConfiguration::isLowRisk(double val) {
			return lowRisk.in_range(val);
		}

		bool SensorConfiguration::isMediumRisk(double val) {
			return (mediumRisk[0].in_range(val) || mediumRisk[1].in_range(val));
		}

		bool SensorConfiguration::isHighRisk(double val) {
			return (highRisk[0].in_range(val) || highRisk[1].in_range(val));
		}

		void SensorConfiguration::setHighRisk(const array<Range, 2> h) {
			highRisk = h;
		}

		Range SensorConfiguration::getLowPercentage() const {
			return lowPercentage;
		}

		void SensorConfiguration::setLowPercentage(const Range lp) {
			lowPercentage = lp;
		}

		Range SensorConfiguration::getMidPercentage() const {
			return midPercentage;
		}

		void SensorConfiguration::setMidPercentage(const Range mp) {
			midPercentage = mp;
		}

		Range SensorConfiguration::getHighPercentage() const {
			return highPercentage;
		}

		void SensorConfiguration::setHighPercentage(const Range hp) {
			highPercentage = hp;
		}

	}
}
