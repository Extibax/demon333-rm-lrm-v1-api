
resource "aws_vpc" "lrm_v2" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name        = "lrm_v2"
    Environment = "shared"
  }
}
resource "aws_instance" "lrm_v2_vpn" {
  ami                    = "ami-099aae505e404f737"
  instance_type          = "t3.small"
  vpc_security_group_ids = [aws_security_group.lrm_v2_vpn_sg.id]
  subnet_id              = aws_subnet.prod_a.id
  key_name               = aws_key_pair.lrm_v2_vpn_key.key_name
  tags = {
    Name        = "lrm-v2-vpn"
    Environment = "shared"
    Proyect     = "lrm"
  }
}
resource "aws_eip" "cheilvpn" {
  # (resource arguments)
  instance = aws_instance.lrm_v2_vpn.id
  tags = {
    Name        = "lrm_v2_vpn_ip"
    Environment = "shared"
    Proyect     = "lrm"
  }
}
resource "aws_route53_zone" "lrm_v2_dns_zone" {
  # (resource arguments)
  name = "cheilbidx.io"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
}

resource "aws_route53_record" "lrm_v2_prod_elb_records" {
  name            = "lrm-api-prod"
  records         = [aws_lb.lrm_v2_prod_elb.dns_name]
  type            = "CNAME"
  allow_overwrite = true
  ttl             = 60
  zone_id         = aws_route53_zone.lrm_v2_dns_zone.zone_id
}
provider "aws" {
  region = "us-east-1"
  alias  = "shared"
  default_tags {
    tags = {
      Environment = "shared"
    }
  }
}
resource "aws_s3_bucket" "etlgscmsales" {
  tags = {
    Name        = "etlgscmsales"
    Environment = "shared"
    Proyect     = "lrm"
  }
}
# resource "aws_amplify_app" "lrm" {
#   name = "lrm"
# }

resource "aws_dynamodb_table" "lrm-cache-l1" {
  name = "cache-layer-1"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
  range_key = "SK"

}
resource "aws_dynamodb_table" "lrm-global-params" {
  table_class = "STANDARD"
  name        = "lrm-global-params"
  tags = {
    Environment = "shared"
    Proyect     = "lrm"
  }
  range_key = "SK"
}
